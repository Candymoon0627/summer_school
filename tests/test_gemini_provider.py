import json
from typing import ClassVar

from app.schemas.lesson import StructuredLesson
from app.services.model_providers.gemini import GeminiEmbeddingProvider, GeminiModelProvider


class FakeResponse:
    text = json.dumps(
        {
            "title": "Fractions with Market Sharing",
            "summary": "Students learn fractions through equal sharing examples.",
            "teaching_objectives": ["Identify halves and quarters."],
            "materials": ["Paper strips"],
            "lesson_flow": [
                {
                    "phase": "Activity",
                    "minutes": 20,
                    "teacher_action": "Model equal sharing.",
                    "student_action": "Divide paper strips.",
                }
            ],
            "local_examples": ["Sharing food at a market."],
            "key_terms_trilingual": [
                {
                    "term_th": "fraction",
                    "helper_ms": "bahagian",
                    "helper_en": "fraction",
                    "teacher_note": "Use objects before symbols.",
                }
            ],
            "student_activity": "Students make halves and quarters.",
            "practice_questions": ["Which is larger, 1/2 or 1/4?"],
            "board_plan": "Draw one whole split into equal parts.",
            "low_resource_plan": "Use chalk and found objects.",
            "safety_notes": "Do not use real student names.",
            "local_knowledge_used": ["Market sharing"],
        }
    )

    class UsageMetadata:
        prompt_token_count = 12
        candidates_token_count = 34

    usage_metadata = UsageMetadata()


class FakeTextModels:
    def generate_content(self, **kwargs):
        assert kwargs["model"] == "gemini-test"
        assert kwargs["config"].response_mime_type == "application/json"
        return FakeResponse()


class FakeClient:
    models = FakeTextModels()


class RetryableGeminiError(Exception):
    status_code = 503


class FakeRetryTextModels:
    def __init__(self) -> None:
        self.calls = 0

    def generate_content(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            raise RetryableGeminiError("temporary high demand")
        assert kwargs["model"] == "gemini-test"
        return FakeResponse()


class FakeRetryClient:
    def __init__(self) -> None:
        self.models = FakeRetryTextModels()


def test_gemini_provider_parses_structured_lesson() -> None:
    provider = GeminiModelProvider(api_key="test-key", model_name="gemini-test", client=FakeClient())

    result = provider.generate_lesson("Subject: math")

    assert isinstance(result.structured_content, StructuredLesson)
    assert result.structured_content.title == "Fractions with Market Sharing"
    assert result.rendered_markdown.startswith("# Fractions with Market Sharing")
    assert result.token_input == 12
    assert result.token_output == 34


def test_gemini_provider_retries_retryable_generation_error() -> None:
    client = FakeRetryClient()
    provider = GeminiModelProvider(
        api_key="test-key",
        model_name="gemini-test",
        client=client,
        retry_delays=(0,),
    )

    result = provider.generate_lesson("Subject: science")

    assert result.structured_content.title == "Fractions with Market Sharing"
    assert client.models.calls == 2


class FakeEmbedding:
    values: ClassVar[list[float]] = [0.1, -0.2, 0.3]


class FakeEmbeddingResponse:
    embeddings: ClassVar[list[FakeEmbedding]] = [FakeEmbedding()]


class FakeEmbeddingModels:
    def generate_content(self, **kwargs):
        raise AssertionError("generate_content should not be called for embeddings")

    def embed_content(self, **kwargs):
        assert kwargs["model"] == "gemini-embedding-test"
        assert kwargs["contents"] == "document text"
        return FakeEmbeddingResponse()


class FakeEmbeddingClient:
    models = FakeEmbeddingModels()


def test_gemini_embedding_provider_returns_float_vector() -> None:
    provider = GeminiEmbeddingProvider(
        api_key="test-key",
        model_name="gemini-embedding-test",
        client=FakeEmbeddingClient(),
    )

    assert provider.embed("document text") == [0.1, -0.2, 0.3]
