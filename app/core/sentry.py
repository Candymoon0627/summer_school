from app.core.config import get_settings


def is_sentry_configured() -> bool:
    return bool(get_settings().sentry_dsn)


def init_sentry() -> bool:
    settings = get_settings()
    if not settings.sentry_dsn:
        return False

    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.rq import RqIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        integrations=[FastApiIntegration(), SqlalchemyIntegration(), RqIntegration()],
        send_default_pii=False,
        traces_sample_rate=settings.sentry_traces_sample_rate,
    )
    return True


def capture_sentry_test_event(source: str = "manual") -> str | None:
    if not is_sentry_configured():
        return None

    import sentry_sdk

    try:
        raise RuntimeError(f"Edu AI Assistant Sentry test error from {source}")
    except RuntimeError as exc:
        event_id = sentry_sdk.capture_exception(exc)
    sentry_sdk.flush(timeout=2)
    return str(event_id) if event_id else None
