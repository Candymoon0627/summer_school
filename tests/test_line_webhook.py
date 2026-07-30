import base64
import hashlib
import hmac
import json

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.main import app
from app.core.config import get_settings
from app.db import models
from app.db.base import Base
from app.schemas.admin import CreateSchoolRequest
from app.services.line_webhook import LineWebhookService
from app.services.onboarding import OnboardingService


def _signature(body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def test_line_webhook_rejects_invalid_signature(monkeypatch) -> None:
    monkeypatch.setenv("LINE_CHANNEL_SECRET", "test-secret")
    get_settings.cache_clear()
    body = {"events": []}

    response = TestClient(app).post(
        "/line/webhook",
        json=body,
        headers={"x-line-signature": "invalid"},
    )

    assert response.status_code == 401


def test_line_webhook_accepts_valid_signature(monkeypatch) -> None:
    monkeypatch.setenv("LINE_CHANNEL_SECRET", "test-secret")
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "")
    get_settings.cache_clear()
    body = json.dumps({"events": []}).encode("utf-8")

    response = TestClient(app).post(
        "/line/webhook",
        content=body,
        headers={
            "content-type": "application/json",
            "x-line-signature": _signature(body, "test-secret"),
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "received"


def test_line_webhook_commits_received_event(monkeypatch) -> None:
    monkeypatch.setenv("LINE_CHANNEL_SECRET", "test-secret")
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "")
    get_settings.cache_clear()
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr("app.api.routes.line.SessionLocal", Session)
    body = json.dumps(
        {
            "events": [
                {
                    "type": "message",
                    "replyToken": "reply-token",
                    "source": {"userId": "line-user-webhook-route"},
                    "message": {"id": "message-route-1", "type": "text", "text": "wrong-code"},
                }
            ]
        }
    ).encode("utf-8")

    response = TestClient(app).post(
        "/line/webhook",
        content=body,
        headers={
            "content-type": "application/json",
            "x-line-signature": _signature(body, "test-secret"),
        },
    )

    with Session() as db:
        events = db.query(models.LineEvent).all()

    assert response.status_code == 200
    assert len(events) == 1
    assert events[0].line_user_id == "line-user-webhook-route"


def test_line_webhook_replies_to_unbound_teacher(monkeypatch) -> None:
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "")
    get_settings.cache_clear()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    replies = []
    monkeypatch.setattr(
        "app.services.line_messaging.LineMessagingService.reply_text",
        lambda self, reply_token, text: replies.append((reply_token, text)),
    )
    payload = {
        "events": [
            {
                "type": "message",
                "replyToken": "reply-token",
                "source": {"userId": "line-user-webhook"},
                "message": {"id": "message-1", "type": "text", "text": "wrong-code"},
            }
        ]
    }
    with Session() as db:
        result = LineWebhookService(db).handle_payload(payload)

    assert result == {"handled": 1, "skipped": 0}
    assert replies
    assert "รหัสเชิญโรงเรียน" in replies[0][1]


def test_line_webhook_creates_text_submission_for_bound_teacher(monkeypatch) -> None:
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "")
    get_settings.cache_clear()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    replies = []
    monkeypatch.setattr(
        "app.services.line_messaging.LineMessagingService.reply_text",
        lambda self, reply_token, text: replies.append((reply_token, text)),
    )

    with Session() as db:
        school = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(name="Webhook Submission School", region_code="pattani", region_name="Pattani")
        )
        OnboardingService(db).bind_teacher_by_school_code(
            line_user_id="line-user-submission",
            school_code=school.school_code,
        )
        payload = {
            "events": [
                {
                    "type": "message",
                    "replyToken": "reply-token",
                    "source": {"userId": "line-user-submission"},
                    "message": {
                        "id": "message-submit-1",
                        "type": "text",
                        "text": "submit: Use a canal example for measurement.",
                    },
                }
            ]
        }

        result = LineWebhookService(db).handle_payload(payload)
        submissions = db.query(models.Submission).all()

    assert result == {"handled": 1, "skipped": 0}
    assert len(submissions) == 1
    assert submissions[0].status == "pending_review"
    assert "ได้รับข้อมูลแล้ว" in replies[0][1]


def test_line_webhook_changes_bound_teacher_language(monkeypatch) -> None:
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "")
    get_settings.cache_clear()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    replies = []
    linked = []
    monkeypatch.setattr(
        "app.services.line_messaging.LineMessagingService.reply_text",
        lambda self, reply_token, text: replies.append((reply_token, text)),
    )
    monkeypatch.setattr(
        "app.services.line_messaging.LineMessagingService.link_rich_menu_for_language",
        lambda self, line_user_id, language: linked.append((line_user_id, language)),
    )

    with Session() as db:
        school = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(name="Language School", region_code="pattani", region_name="Pattani")
        )
        OnboardingService(db).bind_teacher_by_school_code(
            line_user_id="line-user-language",
            school_code=school.school_code,
        )
        payload = {
            "events": [
                {
                    "type": "message",
                    "replyToken": "reply-token",
                    "source": {"userId": "line-user-language"},
                    "message": {"id": "message-language-1", "type": "text", "text": "English"},
                }
            ]
        }

        result = LineWebhookService(db).handle_payload(payload)
        teacher = db.query(models.Teacher).filter_by(line_user_id="line-user-language").one()

    assert result == {"handled": 1, "skipped": 0}
    assert teacher.language_preference == "en"
    assert linked == [("line-user-language", "en")]
    assert replies == [("reply-token", "Language changed to English.")]


def test_line_webhook_prompts_language_choices(monkeypatch) -> None:
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "")
    get_settings.cache_clear()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    prompts = []
    monkeypatch.setattr(
        "app.services.line_messaging.LineMessagingService.reply_language_choices",
        lambda self, reply_token, text: prompts.append((reply_token, text)),
    )

    with Session() as db:
        school = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(name="Language School", region_code="pattani", region_name="Pattani")
        )
        OnboardingService(db).bind_teacher_by_school_code(
            line_user_id="line-user-language-prompt",
            school_code=school.school_code,
        )
        payload = {
            "events": [
                {
                    "type": "message",
                    "replyToken": "reply-token",
                    "source": {"userId": "line-user-language-prompt"},
                    "message": {
                        "id": "message-language-prompt-1",
                        "type": "text",
                        "text": "เปลี่ยนภาษา",
                    },
                }
            ]
        }

        result = LineWebhookService(db).handle_payload(payload)

    assert result == {"handled": 1, "skipped": 0}
    assert prompts
    assert "DOCX" in prompts[0][1]


def test_line_webhook_handles_thai_menu_alias_and_history(monkeypatch) -> None:
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "")
    get_settings.cache_clear()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    replies = []
    menu_cards = []
    monkeypatch.setattr(
        "app.services.line_messaging.LineMessagingService.reply_text",
        lambda self, reply_token, text: replies.append((reply_token, text)),
    )
    monkeypatch.setattr(
        "app.services.line_messaging.LineMessagingService.reply_menu_card",
        lambda self, reply_token, command, language: menu_cards.append(
            (reply_token, command, language)
        ),
    )

    with Session() as db:
        school = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(name="Menu School", region_code="pattani", region_name="Pattani")
        )
        OnboardingService(db).bind_teacher_by_school_code(
            line_user_id="line-user-menu",
            school_code=school.school_code,
        )
        lesson_payload = {
            "events": [
                {
                    "type": "message",
                    "replyToken": "reply-token-lesson",
                    "source": {"userId": "line-user-menu"},
                    "message": {"id": "message-menu-1", "type": "text", "text": "แผนการสอน"},
                }
            ]
        }
        history_payload = {
            "events": [
                {
                    "type": "message",
                    "replyToken": "reply-token-history",
                    "source": {"userId": "line-user-menu"},
                    "message": {"id": "message-menu-2", "type": "text", "text": "/menu_history"},
                }
            ]
        }

        LineWebhookService(db).handle_payload(lesson_payload)
        LineWebhookService(db).handle_payload(history_payload)

    assert menu_cards == [("reply-token-lesson", "lesson", "th")]
    assert "ยังไม่มีประวัติ" in replies[0][1]


def test_line_webhook_replies_with_menu_card_for_english_menu(monkeypatch) -> None:
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "")
    get_settings.cache_clear()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    menu_cards = []
    monkeypatch.setattr(
        "app.services.line_messaging.LineMessagingService.reply_menu_card",
        lambda self, reply_token, command, language: menu_cards.append(
            (reply_token, command, language)
        ),
    )

    with Session() as db:
        school = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(
                name="English Menu School",
                region_code="pattani",
                region_name="Pattani",
            )
        )
        OnboardingService(db).bind_teacher_by_school_code(
            line_user_id="line-user-english-menu",
            school_code=school.school_code,
        )
        teacher = db.query(models.Teacher).filter_by(line_user_id="line-user-english-menu").one()
        teacher.language_preference = "en"
        db.commit()
        payload = {
            "events": [
                {
                    "type": "message",
                    "replyToken": "reply-token-card",
                    "source": {"userId": "line-user-english-menu"},
                    "message": {
                        "id": "message-card-1",
                        "type": "text",
                        "text": "/menu_submit_text",
                    },
                }
            ]
        }

        result = LineWebhookService(db).handle_payload(payload)

    assert result == {"handled": 1, "skipped": 0}
    assert menu_cards == [("reply-token-card", "submit_text", "en")]


def test_line_webhook_lesson_quick_reply_flow_creates_request(monkeypatch) -> None:
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "")
    get_settings.cache_clear()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    replies = []
    enqueued = []
    monkeypatch.setattr(
        "app.services.line_messaging.LineMessagingService.reply_text",
        lambda self, reply_token, text, quick_reply_items=None: replies.append(
            (reply_token, text, quick_reply_items)
        ),
    )
    monkeypatch.setattr(
        "app.services.queue.QueueService.enqueue_lesson_generation",
        lambda self, lesson_request_id: enqueued.append(lesson_request_id) or "test-job-id",
    )

    with Session() as db:
        school = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(
                name="Lesson Flow School",
                region_code="pattani",
                region_name="Pattani",
            )
        )
        OnboardingService(db).bind_teacher_by_school_code(
            line_user_id="line-user-lesson-flow",
            school_code=school.school_code,
        )
        for index, text in enumerate(
            [
                "/lesson_choose_grade",
                "/lesson_grade_5",
                "/lesson_subject_science",
                "plant parts",
            ],
            start=1,
        ):
            LineWebhookService(db).handle_payload(
                {
                    "events": [
                        {
                            "type": "message",
                            "replyToken": f"reply-token-flow-{index}",
                            "source": {"userId": "line-user-lesson-flow"},
                            "message": {
                                "id": f"message-flow-{index}",
                                "type": "text",
                                "text": text,
                            },
                        }
                    ]
                }
            )
        lessons = db.query(models.LessonRequest).all()
        teacher = db.query(models.Teacher).filter_by(line_user_id="line-user-lesson-flow").one()

    assert replies[0][0] == "reply-token-flow-1"
    assert replies[0][2][0]["action"]["text"] == "/lesson_grade_1"
    assert replies[1][0] == "reply-token-flow-2"
    assert replies[1][2][0]["action"]["text"] == "/lesson_subject_math"
    assert replies[2][0] == "reply-token-flow-3"
    assert len(lessons) == 1
    assert lessons[0].grade == 5
    assert lessons[0].subject == "science"
    assert lessons[0].topic == "plant parts"
    assert enqueued == [str(lessons[0].id)]
    assert teacher.note is None


def test_submission_example_does_not_create_submission(monkeypatch) -> None:
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "")
    get_settings.cache_clear()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    replies = []
    monkeypatch.setattr(
        "app.services.line_messaging.LineMessagingService.reply_text",
        lambda self, reply_token, text, quick_reply_items=None: replies.append((reply_token, text)),
    )

    with Session() as db:
        school = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(
                name="Submission Example School",
                region_code="pattani",
                region_name="Pattani",
            )
        )
        OnboardingService(db).bind_teacher_by_school_code(
            line_user_id="line-user-submission-example",
            school_code=school.school_code,
        )
        result = LineWebhookService(db).handle_payload(
            {
                "events": [
                    {
                        "type": "message",
                        "replyToken": "reply-token-example",
                        "source": {"userId": "line-user-submission-example"},
                        "message": {
                            "id": "message-submission-example",
                            "type": "text",
                            "text": "/submission_example",
                        },
                    }
                ]
            }
        )
        submissions = db.query(models.Submission).all()

    assert result == {"handled": 1, "skipped": 0}
    assert submissions == []
    assert replies == [
        (
            "reply-token-example",
            "ตัวอย่าง:\nsubmit: Use a local market example for measuring weight.",
        )
    ]
