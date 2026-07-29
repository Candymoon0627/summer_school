from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, or_, select, update

from app.db.models.lesson import LessonKnowledgeRef, LessonRequest
from app.db.models.media import MediaAsset
from app.db.models.org import School, Teacher
from app.db.session import SessionLocal
from app.services.storage import StorageService

DEFAULT_TEACHER_PREFIXES = ("smoke-user-", "seed-smoke-user-")
DEFAULT_SCHOOL_PREFIXES = ("Smoke Test School ", "Seed RAG Smoke School ")


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean automatically generated smoke-test data.")
    parser.add_argument("--execute", action="store_true", help="Actually delete matched rows.")
    parser.add_argument(
        "--delete-storage-files",
        action="store_true",
        help="Also delete matched media files from the configured storage backend.",
    )
    parser.add_argument(
        "--include-line-smoke-school",
        action="store_true",
        help="Also include the manually used LINE Smoke Test School.",
    )
    args = parser.parse_args()

    with SessionLocal() as db:
        teacher_prefixes = DEFAULT_TEACHER_PREFIXES
        school_prefixes = DEFAULT_SCHOOL_PREFIXES + (
            ("LINE Smoke Test School",) if args.include_line_smoke_school else ()
        )
        teacher_ids = list(
            db.scalars(
                select(Teacher.id).where(
                    or_(
                        *[
                            Teacher.line_user_id.startswith(prefix)
                            for prefix in teacher_prefixes
                        ]
                    )
                )
            )
        )
        school_ids = []
        for prefix in school_prefixes:
            school_ids.extend(db.scalars(select(School.id).where(School.name.startswith(prefix))))

        lesson_ids = list(
            db.scalars(select(LessonRequest.id).where(LessonRequest.teacher_id.in_(teacher_ids)))
        )
        media_assets = list(
            db.scalars(
                select(MediaAsset).where(
                    MediaAsset.owner_type == "lesson_request",
                    MediaAsset.owner_id.in_([str(lesson_id) for lesson_id in lesson_ids]),
                )
            )
        )
        media_ids = [asset.id for asset in media_assets]

        print(
            "MATCHED | "
            f"schools={len(set(school_ids))} teachers={len(teacher_ids)} "
            f"lessons={len(lesson_ids)} media_assets={len(media_ids)}"
        )
        if not args.execute:
            print("DRY-RUN | pass --execute to delete matched rows")
            return

        if args.delete_storage_files:
            storage = StorageService()
            for asset in media_assets:
                storage.delete_file(asset.object_key)

        if lesson_ids:
            db.execute(
                update(LessonRequest)
                .where(LessonRequest.id.in_(lesson_ids))
                .values(docx_media_asset_id=None)
            )
            db.execute(delete(LessonKnowledgeRef).where(LessonKnowledgeRef.lesson_request_id.in_(lesson_ids)))
            db.execute(delete(MediaAsset).where(MediaAsset.id.in_(media_ids)))
            db.execute(delete(LessonRequest).where(LessonRequest.id.in_(lesson_ids)))
        if teacher_ids:
            db.execute(delete(Teacher).where(Teacher.id.in_(teacher_ids)))
        if school_ids:
            db.execute(delete(School).where(School.id.in_(list(set(school_ids)))))
        db.commit()
        print("DELETED | matched smoke-test rows")


if __name__ == "__main__":
    main()
