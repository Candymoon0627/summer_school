import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.session import engine


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Created database tables for local scaffold. Use Alembic migrations for real deployments.")


if __name__ == "__main__":
    main()
