import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml
from pydantic import TypeAdapter

from app.db.session import SessionLocal
from app.schemas.knowledge import KnowledgeSeedItem
from app.services.knowledge import KnowledgeService


def load_seed_file(path: Path) -> list[KnowledgeSeedItem]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return TypeAdapter(list[KnowledgeSeedItem]).validate_python(raw)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import seed knowledge YAML files.")
    parser.add_argument(
        "--file",
        type=Path,
        action="append",
        dest="files",
        help="Import a specific YAML file. Can be passed more than once.",
    )
    args = parser.parse_args()

    seed_dir = Path("data/seed_knowledge")
    paths = args.files or sorted(seed_dir.glob("*.yaml"))
    with SessionLocal() as db:
        service = KnowledgeService(db)
        for path in paths:
            items = load_seed_file(path)
            for item in items:
                service.import_seed_item(item)
            print(f"{path}: imported {len(items)} seed knowledge items")


if __name__ == "__main__":
    main()
