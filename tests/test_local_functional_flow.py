from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db import models
from app.db.base import Base
from app.db.models.media import MediaAsset
from app.schemas.admin import CreateSchoolRequest
from app.services.lesson_generation import LessonGenerationService
from app.services.lesson_requests import LessonRequestService
from app.services.onboarding import OnboardingService
from app.services.queue import QueueService


def test_create_school_bind_teacher_and_create_lesson_request() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    with Session() as db:
        school = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(name="Test School", region_code="pattani", region_name="Pattani")
        )
        assert school.school_code

        bound = OnboardingService(db).bind_teacher_by_school_code(
            line_user_id="line-user-1",
            school_code=school.school_code,
        )
        assert bound is not None
        assert bound.school_name == "Test School"

        result = LessonRequestService(db).create_from_teacher_text(
            line_user_id="line-user-1",
            text="四年级数学 分数",
            enqueue=False,
        )
        assert result["status"] == "queued"
        assert result["lesson_request_id"]

        lesson = LessonGenerationService(db).generate(result["lesson_request_id"])
        assert lesson.status == "completed"
        assert lesson.structured_content["title"]
        assert lesson.rendered_markdown.startswith("#")
        assert lesson.docx_media_asset_id is not None
        assert lesson.completed_at is not None
        assets = list(
            db.scalars(
                select(MediaAsset).where(
                    MediaAsset.owner_type == "lesson_request",
                    MediaAsset.owner_id == str(lesson.id),
                )
            )
        )
        assert {asset.purpose for asset in assets} == {
            "lesson_docx_th",
            "lesson_docx_ms",
            "lesson_docx_en",
        }


def test_lesson_generation_pushes_line_completion_message(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    pushed = []

    monkeypatch.setattr(
        "app.services.line_messaging.LineMessagingService.push_text",
        lambda self, line_user_id, text: pushed.append((line_user_id, text)),
    )

    with Session() as db:
        school = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(name="Test School", region_code="pattani", region_name="Pattani")
        )
        OnboardingService(db).bind_teacher_by_school_code(
            line_user_id="line-user-push",
            school_code=school.school_code,
        )
        result = LessonRequestService(db).create_from_teacher_text(
            line_user_id="line-user-push",
            text="Grade 4 math fractions",
            enqueue=False,
        )

        LessonGenerationService(db).generate(result["lesson_request_id"])

    assert pushed
    assert pushed[0][0] == "line-user-push"
    assert "แผนการสอนพร้อมแล้ว:" in pushed[0][1]
    assert "ดาวน์โหลด DOCX:" in pushed[0][1]
    assert "Thai:" in pushed[0][1]
    assert "Local Malay:" not in pushed[0][1]
    assert "English:" not in pushed[0][1]


def test_lesson_generation_pushes_preferred_language_completion_message(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    pushed = []

    monkeypatch.setattr(
        "app.services.line_messaging.LineMessagingService.push_text",
        lambda self, line_user_id, text: pushed.append((line_user_id, text)),
    )

    with Session() as db:
        school = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(name="Test School", region_code="pattani", region_name="Pattani")
        )
        OnboardingService(db).bind_teacher_by_school_code(
            line_user_id="line-user-push-en",
            school_code=school.school_code,
        )
        teacher = db.query(models.Teacher).filter_by(line_user_id="line-user-push-en").one()
        teacher.language_preference = "en"
        db.commit()
        result = LessonRequestService(db).create_from_teacher_text(
            line_user_id="line-user-push-en",
            text="Grade 4 math fractions",
            enqueue=False,
            language="en",
        )

        LessonGenerationService(db).generate(result["lesson_request_id"])

    assert pushed
    assert pushed[0][0] == "line-user-push-en"
    assert "Lesson plan ready:" in pushed[0][1]
    assert "Download DOCX:" in pushed[0][1]
    assert "English:" in pushed[0][1]
    assert "Thai:" not in pushed[0][1]
    assert "Local Malay:" not in pushed[0][1]


def test_lesson_generation_stays_completed_when_line_push_fails(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    def fail_push(self, line_user_id, text):
        raise RuntimeError("line push failed")

    monkeypatch.setattr("app.services.line_messaging.LineMessagingService.push_text", fail_push)

    with Session() as db:
        school = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(name="Test School", region_code="pattani", region_name="Pattani")
        )
        OnboardingService(db).bind_teacher_by_school_code(
            line_user_id="line-user-push-fail",
            school_code=school.school_code,
        )
        result = LessonRequestService(db).create_from_teacher_text(
            line_user_id="line-user-push-fail",
            text="Grade 4 math fractions",
            enqueue=False,
        )

        lesson = LessonGenerationService(db).generate(result["lesson_request_id"])

    assert lesson.status == "completed"


def test_lesson_generation_marks_failed_when_provider_fails(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    class FailingProvider:
        provider_name = "failing"
        model_name = "failing-model"

        def generate_lesson(self, prompt: str):
            raise RuntimeError("provider failed")

    monkeypatch.setattr(
        "app.services.lesson_generation.get_text_model_provider",
        lambda: FailingProvider(),
    )
    monkeypatch.setattr(
        "app.services.line_messaging.LineMessagingService.push_text",
        lambda self, line_user_id, text: None,
    )

    with Session() as db:
        school = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(name="Test School", region_code="pattani", region_name="Pattani")
        )
        OnboardingService(db).bind_teacher_by_school_code(
            line_user_id="line-user-provider-fail",
            school_code=school.school_code,
        )
        result = LessonRequestService(db).create_from_teacher_text(
            line_user_id="line-user-provider-fail",
            text="Grade 4 math fractions",
            enqueue=False,
        )

        try:
            LessonGenerationService(db).generate(result["lesson_request_id"])
        except RuntimeError as exc:
            assert "provider failed" in str(exc)
        else:
            raise AssertionError("Expected provider failure.")

        lesson = db.get(models.LessonRequest, UUID(result["lesson_request_id"]))

    assert lesson.status == "failed"
    assert "provider failed" in lesson.error_message


def test_create_lesson_request_returns_queue_job_id_when_enqueued(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    monkeypatch.setattr(
        QueueService,
        "enqueue_lesson_generation",
        lambda self, lesson_request_id: f"job-{lesson_request_id}",
    )

    with Session() as db:
        school = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(name="Test School", region_code="pattani", region_name="Pattani")
        )
        OnboardingService(db).bind_teacher_by_school_code(
            line_user_id="line-user-1",
            school_code=school.school_code,
        )

        result = LessonRequestService(db).create_from_teacher_text(
            line_user_id="line-user-1",
            text="Grade 4 math fractions",
            enqueue=True,
        )

        assert result["status"] == "queued"
        assert result["queue_job_id"] == f"job-{result['lesson_request_id']}"
