from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def engine_kwargs(database_url: str) -> dict:
    kwargs = {"pool_pre_ping": True}
    url = make_url(database_url)
    if url.drivername == "postgresql+psycopg":
        kwargs["connect_args"] = {"prepare_threshold": None}
    return kwargs


engine = create_engine(get_settings().database_url, **engine_kwargs(get_settings().database_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
