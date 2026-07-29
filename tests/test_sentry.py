from fastapi.testclient import TestClient

from app.api.main import app
from app.core.config import get_settings
from app.core.sentry import capture_sentry_test_event, is_sentry_configured

AUTH = ("admin", "test-admin-password")


def test_sentry_helpers_return_not_configured_without_dsn(monkeypatch) -> None:
    monkeypatch.setenv("SENTRY_DSN", "")
    get_settings.cache_clear()

    assert is_sentry_configured() is False
    assert capture_sentry_test_event() is None


def test_admin_sentry_test_endpoint_returns_not_configured(monkeypatch) -> None:
    monkeypatch.setenv("SENTRY_DSN", "")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("ADMIN_USERNAME", AUTH[0])
    monkeypatch.setenv("ADMIN_PASSWORD", AUTH[1])
    monkeypatch.setenv("ADMIN_ROLE", "super_admin")
    get_settings.cache_clear()

    response = TestClient(app).post("/admin/dev/sentry-test", auth=AUTH)

    assert response.status_code == 200
    assert response.json() == {"status": "not_configured", "event_id": None}


def test_admin_sentry_test_endpoint_returns_event_id(monkeypatch) -> None:
    monkeypatch.setenv("SENTRY_DSN", "https://public@example.com/1")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("ADMIN_USERNAME", AUTH[0])
    monkeypatch.setenv("ADMIN_PASSWORD", AUTH[1])
    monkeypatch.setenv("ADMIN_ROLE", "super_admin")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "app.api.routes.admin.capture_sentry_test_event",
        lambda source: "test-event-id",
    )

    response = TestClient(app).post("/admin/dev/sentry-test", auth=AUTH)

    assert response.status_code == 200
    assert response.json() == {"status": "sent", "event_id": "test-event-id"}


def test_admin_sentry_test_endpoint_is_development_only(monkeypatch) -> None:
    monkeypatch.setenv("SENTRY_DSN", "https://public@example.com/1")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("ADMIN_USERNAME", AUTH[0])
    monkeypatch.setenv("ADMIN_PASSWORD", AUTH[1])
    monkeypatch.setenv("ADMIN_ROLE", "super_admin")
    get_settings.cache_clear()

    response = TestClient(app).post("/admin/dev/sentry-test", auth=AUTH)

    assert response.status_code == 403
