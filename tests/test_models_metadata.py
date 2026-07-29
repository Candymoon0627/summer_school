from sqlalchemy import create_engine

from app.db import models  # noqa: F401
from app.db.base import Base


def test_metadata_can_create_tables_on_sqlite() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

