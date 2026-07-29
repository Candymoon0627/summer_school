from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, or_, select

from app.db.models.duplicate import DuplicateCandidate
from app.db.models.knowledge import KnowledgeChunk, KnowledgeItem, KnowledgeItemVersion
from app.db.models.lesson import LessonKnowledgeRef
from app.db.session import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete seed knowledge imported for a test batch.")
    parser.add_argument("--batch-id", required=True, help="Batch id contained in source_note.")
    parser.add_argument(
        "--source-type",
        default="oer_synthetic_test",
        help="KnowledgeItem.source_type to match.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print what would be deleted.")
    args = parser.parse_args()

    with SessionLocal() as db:
        item_ids = list(
            db.scalars(
                select(KnowledgeItem.id).where(
                    KnowledgeItem.source_type == args.source_type,
                    KnowledgeItem.source_note.contains(args.batch_id),
                )
            )
        )
        print(f"Matched {len(item_ids)} knowledge items for batch {args.batch_id}.")
        if args.dry_run or not item_ids:
            return

        db.execute(delete(LessonKnowledgeRef).where(LessonKnowledgeRef.knowledge_item_id.in_(item_ids)))
        db.execute(
            delete(DuplicateCandidate).where(
                or_(
                    DuplicateCandidate.knowledge_item_id.in_(item_ids),
                    DuplicateCandidate.candidate_item_id.in_(item_ids),
                )
            )
        )
        db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.knowledge_item_id.in_(item_ids)))
        db.execute(
            delete(KnowledgeItemVersion).where(KnowledgeItemVersion.knowledge_item_id.in_(item_ids))
        )
        db.execute(delete(KnowledgeItem).where(KnowledgeItem.id.in_(item_ids)))
        db.commit()
        print(f"Deleted {len(item_ids)} knowledge items for batch {args.batch_id}.")


if __name__ == "__main__":
    main()
