import logging
from datetime import UTC, datetime
from typing import ClassVar
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.lesson import LessonRequest
from app.db.models.media import MediaAsset
from app.repositories.lesson import LessonRepository
from app.repositories.media import MediaRepository
from app.repositories.org import OrgRepository
from app.services.docx_export import DocxExportService
from app.services.language import normalize_language
from app.services.language import text as localized_text
from app.services.line_messaging import LineMessagingService
from app.services.model_registry import get_text_model_provider
from app.services.rag import RagService
from app.services.storage import StorageService

logger = logging.getLogger(__name__)


class LessonGenerationService:
    prompt_version = "lesson_generation_v1"
    docx_languages: ClassVar[dict[str, str]] = {
        "th": "Thai",
        "ms": "Local Malay",
        "en": "English",
    }

    def __init__(self, db: Session, *, notify_teacher: bool = True) -> None:
        self.db = db
        self.notify_teacher = notify_teacher
        self.rag = RagService(db)
        self.docx = DocxExportService()
        self.storage = StorageService()
        self.lessons = LessonRepository(db)
        self.media = MediaRepository(db)
        self.orgs = OrgRepository(db)
        self.messages = LineMessagingService()

    def generate(self, lesson_request_id: UUID | str) -> LessonRequest:
        if isinstance(lesson_request_id, str):
            lesson_request_id = UUID(lesson_request_id)
        lesson_request = self.db.get(LessonRequest, lesson_request_id)
        if lesson_request is None:
            raise ValueError(f"Lesson request not found: {lesson_request_id}")

        lesson_request.status = "running"
        self.db.commit()

        try:
            retrieved, confidence = self.rag.retrieve_for_lesson(
                teacher_id=str(lesson_request.teacher_id),
                school_id=str(lesson_request.school_id),
                region_id=str(lesson_request.region_id),
                subject=lesson_request.subject or "math",
                grade=lesson_request.grade or 4,
                topic=lesson_request.topic or lesson_request.raw_user_input,
            )
            prompt = self._build_prompt(lesson_request, retrieved, confidence)
            provider = get_text_model_provider()
            result = provider.generate_lesson(prompt)

            lesson_request.structured_content = result.structured_content.model_dump()
            lesson_request.rendered_markdown = result.rendered_markdown
            lesson_request.model_provider = getattr(provider, "provider_name", "unknown")
            lesson_request.model_name = getattr(provider, "model_name", "unknown")
            lesson_request.prompt_version = self.prompt_version
            lesson_request.rag_strategy_version = self.rag.strategy_version
            lesson_request.rag_confidence = confidence
            lesson_request.token_input = result.token_input
            lesson_request.token_output = result.token_output
            self.lessons.replace_knowledge_refs(lesson_request.id, retrieved)

            primary_asset = self._export_docx_assets(lesson_request, result.structured_content)
            lesson_request.docx_media_asset_id = primary_asset.id

            lesson_request.status = "completed"
            lesson_request.completed_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(lesson_request)
        except Exception as exc:
            self._mark_failed(lesson_request.id, exc)
            raise

        if self.notify_teacher:
            self._safe_notify_teacher(lesson_request)
        return lesson_request

    def _mark_failed(self, lesson_request_id: UUID, exc: Exception) -> None:
        self.db.rollback()
        lesson_request = self.db.get(LessonRequest, lesson_request_id)
        if lesson_request is None:
            return
        lesson_request.status = "failed"
        lesson_request.error_message = str(exc)[:4000]
        self.db.commit()
        if self.notify_teacher:
            self._safe_notify_failure(lesson_request)

    def _safe_notify_teacher(self, lesson_request: LessonRequest) -> None:
        try:
            self._notify_teacher(lesson_request)
        except Exception:
            logger.exception("Failed to send LINE completion notification for %s", lesson_request.id)

    def _safe_notify_failure(self, lesson_request: LessonRequest) -> None:
        try:
            teacher = self.orgs.get_teacher_by_id(lesson_request.teacher_id)
            if not teacher or not teacher.line_user_id:
                return
            self.messages.push_text(
                teacher.line_user_id,
                localized_text("lesson_failed", teacher.language_preference),
            )
        except Exception:
            logger.exception("Failed to send LINE failure notification for %s", lesson_request.id)

    def _notify_teacher(self, lesson_request: LessonRequest) -> None:
        teacher = self.orgs.get_teacher_by_id(lesson_request.teacher_id)
        if not teacher or not teacher.line_user_id or not lesson_request.docx_media_asset_id:
            return
        assets = self.media.lesson_docx_assets(lesson_request.id)
        if not assets:
            return
        language = normalize_language(teacher.language_preference)
        structured = lesson_request.structured_content or {}
        title = self._localized_line(
            structured.get("title_trilingual"),
            structured.get("title"),
            language,
        )
        summary = self._localized_line(
            structured.get("summary_trilingual"),
            structured.get("summary"),
            language,
        )
        links = self._download_links(assets, language)
        self.messages.push_text(
            teacher.line_user_id,
            (
                f"{localized_text('lesson_ready', language)}\n{title}\n\n"
                f"{summary[:1200]}\n\n"
                f"{localized_text('download_docx', language)}\n{links}"
            ),
        )

    def _export_docx_assets(self, lesson_request: LessonRequest, lesson) -> MediaAsset:
        primary_asset = None
        for language in self.docx_languages:
            docx_path = self.docx.export_lesson(lesson, "lesson", language=language)
            object_key = f"lesson_docx/{docx_path.name}"
            self.storage.put_file(docx_path, object_key)
            asset = self.media.create_lesson_docx_asset(
                lesson_request_id=lesson_request.id,
                object_key=object_key,
                original_filename=docx_path.name,
                storage_provider=get_settings().storage_provider,
                file_size=docx_path.stat().st_size if docx_path.exists() else None,
                purpose=f"lesson_docx_{language}",
            )
            if language == "th":
                primary_asset = asset
        if primary_asset is None:
            raise RuntimeError("Thai DOCX asset was not created.")
        return primary_asset

    def _download_links(self, assets: list[MediaAsset], language: str) -> str:
        by_purpose = {asset.purpose: asset for asset in assets}
        language = normalize_language(language)
        asset = by_purpose.get(f"lesson_docx_{language}")
        if asset:
            signed_url = self.storage.signed_url(asset.object_key, expires_in=60 * 60 * 24)
            return f"{self.docx_languages[language]}: {signed_url}"

        lines = []
        for fallback_language, label in self.docx_languages.items():
            fallback_asset = by_purpose.get(f"lesson_docx_{fallback_language}")
            if not fallback_asset:
                continue
            signed_url = self.storage.signed_url(fallback_asset.object_key, expires_in=60 * 60 * 24)
            lines.append(f"{label}: {signed_url}")
        return "\n".join(lines)

    def _localized_line(
        self,
        value: dict | None,
        fallback: str | None,
        language: str,
    ) -> str:
        if not value:
            return fallback or "Your lesson plan"
        language = normalize_language(language)
        return value.get(language) or fallback or "Your lesson plan"

    def _build_prompt(self, lesson_request: LessonRequest, retrieved: list, confidence: str) -> str:
        context = "\n".join(f"- {item.title}: {item.content}" for item in retrieved)
        return f"""Generate a structured lesson plan.

Subject: {lesson_request.subject}
Grade: {lesson_request.grade}
Topic: {lesson_request.topic or lesson_request.raw_user_input}
Duration: {lesson_request.duration_minutes}
Language mode: {lesson_request.language_mode}
RAG confidence: {confidence}

Retrieved local knowledge:
{context or "No sufficiently matching local knowledge was found."}
"""
