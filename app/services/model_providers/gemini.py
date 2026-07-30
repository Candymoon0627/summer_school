import json
import logging
import re
import time
from collections.abc import Callable
from typing import Any

from google import genai
from google.genai import types

from app.core.config import get_settings
from app.schemas.lesson import LessonGenerationResult, StructuredLesson
from app.services.model_providers.base import EmbeddingProvider, ModelProvider
from app.services.model_providers.mock import render_lesson_markdown

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
DEFAULT_RETRY_DELAYS_SECONDS = (1.0, 3.0, 8.0)


class GeminiModelProvider(ModelProvider):
    provider_name = "gemini"
    default_model = "gemini-3.6-flash"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model_name: str | None = None,
        client: Any | None = None,
        retry_delays: tuple[float, ...] | None = None,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for the Gemini provider.")

        configured_model = model_name or settings.active_text_model_name
        self.model_name = (
            configured_model
            if configured_model and not configured_model.startswith("mock-")
            else self.default_model
        )
        self.client = client or genai.Client(api_key=self.api_key)
        self.retry_delays = (
            DEFAULT_RETRY_DELAYS_SECONDS if retry_delays is None else retry_delays
        )

    def generate_lesson(self, prompt: str) -> LessonGenerationResult:
        response = _call_with_retry(
            lambda: self.client.models.generate_content(
                model=self.model_name,
                contents=self._lesson_prompt(prompt),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=StructuredLesson,
                    max_output_tokens=16000,
                ),
            ),
            operation="gemini.generate_lesson",
            retry_delays=self.retry_delays,
        )
        lesson = StructuredLesson.model_validate_json(self._response_text(response))
        return LessonGenerationResult(
            structured_content=lesson,
            rendered_markdown=render_lesson_markdown(lesson),
            token_input=self._usage_count(response, "prompt_token_count"),
            token_output=self._usage_count(response, "candidates_token_count"),
        )

    def classify_json(self, prompt: str) -> dict:
        response = _call_with_retry(
            lambda: self.client.models.generate_content(
                model=self.model_name,
                contents=f"{prompt}\n\nReturn a single JSON object only.",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    max_output_tokens=1000,
                ),
            ),
            operation="gemini.classify_json",
            retry_delays=self.retry_delays,
        )
        return json.loads(self._extract_json_object(self._response_text(response)))

    def _lesson_prompt(self, prompt: str) -> str:
        return f"""You are generating a practical lesson plan for a teacher.

Return only JSON matching the requested schema. Keep the lesson classroom-ready,
localized when local context is available, usable in low-resource classrooms,
and avoid using real student or family names.

The lesson must be trilingual:
- Thai is the primary classroom language.
- Local Malay is a helper language for teacher/student explanation.
- English is a helper language for academic terms and review.
- Populate both the legacy fields such as title, summary, teaching_objectives, and the structured
  trilingual fields such as title_trilingual, summary_trilingual, teaching_objectives_trilingual,
  materials_trilingual, lesson_flow_trilingual, local_examples_trilingual,
  student_activity_trilingual, practice_questions_trilingual, board_plan_trilingual,
  low_resource_plan_trilingual, and safety_notes_trilingual.
- For every TrilingualText object, set th to Thai, ms to local Malay, and en to English.
- Keep the Thai text natural and complete; Malay and English can be shorter but must convey the
  same instructional intent.
- Keep every list concise: 2-4 teaching objectives, 2-4 materials, 3-5 lesson flow steps, 2-4
  local examples, 2-4 practice questions, and 3-5 key terms.
- Keep each Thai/Malay/English text value to one or two sentences.

{prompt}
"""

    def _response_text(self, response: Any) -> str:
        text = getattr(response, "text", None)
        if not text:
            raise ValueError("Gemini returned an empty response.")
        return text.strip()

    def _usage_count(self, response: Any, field_name: str) -> int:
        usage = getattr(response, "usage_metadata", None)
        value = getattr(usage, field_name, 0) if usage else 0
        return int(value or 0)

    def _extract_json_object(self, text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
            stripped = re.sub(r"\s*```$", "", stripped)
        return stripped


class GeminiEmbeddingProvider(EmbeddingProvider):
    provider_name = "gemini"
    default_model = "gemini-embedding-2"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model_name: str | None = None,
        output_dimensionality: int | None = None,
        client: Any | None = None,
        retry_delays: tuple[float, ...] | None = None,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini embeddings.")

        configured_model = model_name or settings.active_embedding_model
        self.model_name = (
            configured_model
            if configured_model and not configured_model.startswith("mock-")
            else self.default_model
        )
        self.output_dimensionality = output_dimensionality
        self.client = client or genai.Client(api_key=self.api_key)
        self.retry_delays = (
            DEFAULT_RETRY_DELAYS_SECONDS if retry_delays is None else retry_delays
        )

    def embed(self, text: str) -> list[float]:
        config = None
        if self.output_dimensionality:
            config = types.EmbedContentConfig(output_dimensionality=self.output_dimensionality)

        response = _call_with_retry(
            lambda: self.client.models.embed_content(
                model=self.model_name,
                contents=text,
                config=config,
            ),
            operation="gemini.embed",
            retry_delays=self.retry_delays,
        )
        embeddings = getattr(response, "embeddings", None)
        if not embeddings:
            raise ValueError("Gemini returned no embeddings.")
        values = getattr(embeddings[0], "values", None)
        if not values:
            raise ValueError("Gemini returned an empty embedding.")
        return [float(value) for value in values]


def _call_with_retry(
    call: Callable[[], Any],
    *,
    operation: str,
    retry_delays: tuple[float, ...],
) -> Any:
    for attempt in range(len(retry_delays) + 1):
        try:
            return call()
        except Exception as exc:
            if attempt >= len(retry_delays) or not _is_retryable_gemini_error(exc):
                raise
            delay = retry_delays[attempt]
            logger.warning(
                "%s failed with retryable Gemini error on attempt %s/%s; retrying in %.1fs: %s",
                operation,
                attempt + 1,
                len(retry_delays) + 1,
                delay,
                exc,
            )
            time.sleep(delay)
    raise RuntimeError(f"{operation} retry loop exited unexpectedly.")


def _is_retryable_gemini_error(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if isinstance(status_code, int) and status_code in RETRYABLE_STATUS_CODES:
        return True

    response = getattr(exc, "response", None)
    response_status = getattr(response, "status_code", None)
    return isinstance(response_status, int) and response_status in RETRYABLE_STATUS_CODES
