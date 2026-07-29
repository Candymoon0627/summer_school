from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
from sqlalchemy import func, select

from app.db.models.knowledge import KnowledgeChunk, KnowledgeItem
from app.db.models.lesson import LessonKnowledgeRef
from app.db.models.media import MediaAsset
from app.db.session import SessionLocal
from app.schemas.admin import CreateSchoolRequest
from app.services.lesson_generation import LessonGenerationService
from app.services.lesson_requests import LessonRequestService
from app.services.onboarding import OnboardingService
from app.services.storage import StorageService


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test remote seed RAG lesson generation.")
    parser.add_argument("--batch-id", default="pattani-test-v1-80")
    parser.add_argument("--subject", default="math")
    parser.add_argument("--grade", type=int, default=4)
    parser.add_argument("--topic", default="fractions")
    args = parser.parse_args()

    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    line_user_id = f"seed-smoke-user-{stamp}"

    with SessionLocal() as db:
        item_count = db.scalar(
            select(func.count())
            .select_from(KnowledgeItem)
            .where(
                KnowledgeItem.source_type == "oer_synthetic_test",
                KnowledgeItem.source_note.contains(args.batch_id),
                KnowledgeItem.is_deleted.is_(False),
            )
        )
        chunk_count = db.scalar(
            select(func.count())
            .select_from(KnowledgeChunk)
            .join(KnowledgeItem, KnowledgeItem.id == KnowledgeChunk.knowledge_item_id)
            .where(
                KnowledgeItem.source_note.contains(args.batch_id),
                KnowledgeChunk.active.is_(True),
            )
        )
        if item_count == 0 or chunk_count == 0:
            raise RuntimeError(f"Seed batch {args.batch_id} is not imported and embedded.")
        print(f"PASS | seed batch available | items={item_count} active_chunks={chunk_count}")

        school = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(
                name=f"Seed RAG Smoke School {stamp}",
                region_code="pattani",
                region_name="Pattani",
                country_code="th",
                resource_level="low",
            )
        )
        teacher = OnboardingService(db).bind_teacher_by_school_code(
            line_user_id=line_user_id,
            school_code=school.school_code,
            display_name="Seed RAG Smoke Teacher",
        )
        if teacher is None:
            raise RuntimeError("Teacher binding failed.")
        print(f"PASS | teacher bound | teacher_id={teacher.teacher_id}")

        request = LessonRequestService(db).create_from_teacher_text(
            line_user_id=line_user_id,
            text=f"Grade {args.grade} {args.subject} {args.topic}, 45 minutes, low-resource classroom",
            enqueue=False,
        )
        if request["status"] != "queued":
            raise RuntimeError(f"Lesson request was not queued: {request}")
        print(f"PASS | lesson request created | lesson_request_id={request['lesson_request_id']}")

        lesson = LessonGenerationService(db, notify_teacher=False).generate(
            request["lesson_request_id"]
        )
        if lesson.status != "completed" or not lesson.docx_media_asset_id:
            raise RuntimeError(f"Lesson generation failed: status={lesson.status}")
        if lesson.rag_confidence not in {"medium", "high"}:
            raise RuntimeError(f"Unexpected RAG confidence: {lesson.rag_confidence}")
        print(
            "PASS | lesson generated | "
            f"rag_confidence={lesson.rag_confidence} model={lesson.model_provider}:{lesson.model_name}"
        )

        refs = list(
            db.scalars(
                select(LessonKnowledgeRef)
                .join(KnowledgeItem, KnowledgeItem.id == LessonKnowledgeRef.knowledge_item_id)
                .where(
                    LessonKnowledgeRef.lesson_request_id == lesson.id,
                    KnowledgeItem.source_note.contains(args.batch_id),
                )
                .order_by(LessonKnowledgeRef.rank)
            )
        )
        if not refs:
            raise RuntimeError("Lesson did not record references to the seed batch.")
        print(f"PASS | lesson knowledge refs recorded | refs={len(refs)} top_score={refs[0].relevance_score:.3f}")

        assets = list(
            db.scalars(
                select(MediaAsset)
                .where(MediaAsset.owner_id == str(lesson.id), MediaAsset.media_type == "docx")
                .order_by(MediaAsset.purpose)
            )
        )
        purposes = {asset.purpose for asset in assets}
        expected_purposes = {"lesson_docx_th", "lesson_docx_ms", "lesson_docx_en"}
        if purposes != expected_purposes:
            raise RuntimeError(f"Expected 3 language DOCX assets, got {sorted(purposes)}")
        for asset in assets:
            signed_url = StorageService().signed_url(asset.object_key, expires_in=120)
            download = httpx.get(signed_url, timeout=30)
            download.raise_for_status()
            if not download.content:
                raise RuntimeError(f"Signed DOCX download returned empty content: {asset.purpose}")
        print(
            "PASS | storage upload and signed downloads | "
            f"assets={len(assets)} purposes={','.join(sorted(purposes))}"
        )


if __name__ == "__main__":
    main()
