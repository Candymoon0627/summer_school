from app.db.session import engine_kwargs


def test_psycopg_engine_disables_prepared_statements() -> None:
    kwargs = engine_kwargs("postgresql+psycopg://user:pass@example.com:6543/postgres")

    assert kwargs["pool_pre_ping"] is True
    assert kwargs["connect_args"] == {"prepare_threshold": None}


def test_sqlite_engine_does_not_use_psycopg_connect_args() -> None:
    kwargs = engine_kwargs("sqlite+pysqlite:///:memory:")

    assert kwargs == {"pool_pre_ping": True}
