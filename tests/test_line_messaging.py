import httpx

from app.core.config import get_settings
from app.services.line_messaging import LineMessagingService


def test_link_rich_menu_uses_messaging_api_host(monkeypatch) -> None:
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "test-token")
    monkeypatch.setenv("LINE_RICH_MENU_ID_EN", "richmenu-en")
    get_settings.cache_clear()
    calls = []

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

    class FakeClient:
        def __init__(self, *, timeout: int) -> None:
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

        def post(self, url: str, json: dict, headers: dict) -> FakeResponse:
            calls.append((url, json, headers))
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)

    LineMessagingService().link_rich_menu_for_language("line-user", "en")

    assert calls == [
        (
            "https://api.line.me/v2/bot/user/line-user/richmenu/richmenu-en",
            {},
            {
                "Authorization": "Bearer test-token",
                "Content-Type": "application/json",
            },
        )
    ]


def test_reply_menu_card_sends_flex_with_quick_replies(monkeypatch) -> None:
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "test-token")
    get_settings.cache_clear()
    calls = []

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

    class FakeClient:
        def __init__(self, *, timeout: int) -> None:
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

        def post(self, url: str, json: dict, headers: dict) -> FakeResponse:
            calls.append((url, json, headers))
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)

    LineMessagingService().reply_menu_card("reply-token", command="lesson", language="en")

    url, payload, headers = calls[0]
    message = payload["messages"][0]
    assert url == "https://api.line.me/v2/bot/message/reply"
    assert payload["replyToken"] == "reply-token"
    assert headers["Authorization"] == "Bearer test-token"
    assert message["type"] == "flex"
    assert message["altText"] == "Generate Lesson"
    assert message["contents"]["type"] == "bubble"
    assert message["contents"]["footer"]["contents"][0]["action"]["text"] == "/lesson_choose_grade"
    assert message["quickReply"]["items"][0]["action"]["text"] == "/menu_history"
