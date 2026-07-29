from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.services.publishing_batch import KnowledgeBatchPublishingService


def main() -> None:
    parser = argparse.ArgumentParser(description="Dry-run or publish knowledge items to GitHub.")
    parser.add_argument("--region", dest="region_code", help="Filter by region code, e.g. pattani.")
    parser.add_argument("--subject", help="Filter by subject, e.g. math.")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--allow-test-data", action="store_true")
    parser.add_argument("--allow-warnings", action="store_true")
    parser.add_argument("--execute", action="store_true", help="Actually write to GitHub.")
    args = parser.parse_args()

    with SessionLocal() as db:
        result = KnowledgeBatchPublishingService(db).publish(
            region_code=args.region_code,
            subject=args.subject,
            allow_test_data=args.allow_test_data,
            allow_warnings=args.allow_warnings,
            limit=args.limit,
            dry_run=not args.execute,
        )

    mode = "EXECUTE" if args.execute else "DRY-RUN"
    print(f"{mode} | candidates={len(result.candidates)} published={len(result.published)}")
    for candidate in result.candidates:
        warnings = ",".join(candidate.warnings) if candidate.warnings else "-"
        print(
            f"- {candidate.id} | {candidate.subject}/{candidate.topic} | "
            f"{candidate.title} | path={candidate.github_path} | warnings={warnings}"
        )


if __name__ == "__main__":
    main()
