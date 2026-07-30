from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.main import app
from app.api.routes import admin
from app.core import admin_auth
from app.core.config import get_settings
from app.db import models
from app.db.base import Base
from app.schemas.admin import CreateSchoolRequest
from app.schemas.knowledge import KnowledgeSeedItem
from app.services.knowledge import KnowledgeService
from app.services.lesson_generation import LessonGenerationService
from app.services.lesson_requests import LessonRequestService
from app.services.onboarding import OnboardingService

AUTH = ("admin", "test-admin-password")


def _client_with_seed_data(monkeypatch):
    monkeypatch.setenv("ACTIVE_TEXT_MODEL_PROVIDER", "mock")
    monkeypatch.setenv("ACTIVE_EMBEDDING_PROVIDER", "mock")
    monkeypatch.setenv("GITHUB_REPO", "")
    monkeypatch.setenv("GITHUB_TOKEN", "")
    monkeypatch.setenv("ADMIN_USERNAME", AUTH[0])
    monkeypatch.setenv("ADMIN_PASSWORD", AUTH[1])
    monkeypatch.setenv("ADMIN_ROLE", "super_admin")
    get_settings.cache_clear()
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(admin, "SessionLocal", Session)
    monkeypatch.setattr(admin_auth, "SessionLocal", Session)

    with Session() as db:
        school = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(name="Admin Test School", region_code="pattani", region_name="Pattani")
        )
        OnboardingService(db).bind_teacher_by_school_code(
            line_user_id="admin-line-user",
            school_code=school.school_code,
        )
        request = LessonRequestService(db).create_from_teacher_text(
            line_user_id="admin-line-user",
            text="Grade 4 science water cycle",
            enqueue=False,
        )
        LessonGenerationService(db, notify_teacher=False).generate(request["lesson_request_id"])
        KnowledgeService(db).import_seed_item(
            KnowledgeSeedItem(
                knowledge_type="local_example",
                title="Admin publish candidate",
                region_code="pattani",
                visibility_scope="shared_region",
                subject="science",
                topic="water cycle",
                target_grade=4,
                grade_min=4,
                grade_max=4,
                content_th="วัฏจักรน้ำ",
                content_ms="Kitaran air",
                content_en="Water cycle",
                source_note="admin route test",
                verified=True,
            )
        )

    return TestClient(app)


def test_admin_overview_lessons_and_publishing_candidates(monkeypatch) -> None:
    client = _client_with_seed_data(monkeypatch)

    unauthenticated = client.get("/admin/overview")
    assert unauthenticated.status_code == 401

    overview = client.get("/admin/overview", auth=AUTH)
    assert overview.status_code == 200
    assert overview.json()["counts"]["schools"] == 1
    assert overview.json()["lesson_status"]["completed"] == 1

    lessons = client.get("/admin/lessons", auth=AUTH)
    assert lessons.status_code == 200
    lesson_id = lessons.json()["items"][0]["id"]
    assert lessons.json()["items"][0]["status"] == "completed"

    detail = client.get(f"/admin/lessons/{lesson_id}", auth=AUTH)
    assert detail.status_code == 200
    assert {asset["purpose"] for asset in detail.json()["docx_assets"]} == {
        "lesson_docx_th",
        "lesson_docx_ms",
        "lesson_docx_en",
    }

    candidates = client.get(
        "/admin/publishing/candidates?region=pattani&subject=science",
        auth=AUTH,
    )
    assert candidates.status_code == 200
    assert candidates.json()["items"][0]["title"] == "Admin publish candidate"


def test_admin_batch_publish_execute_uses_mock_github_without_credentials(monkeypatch) -> None:
    client = _client_with_seed_data(monkeypatch)

    response = client.post(
        "/admin/publishing/batch?region=pattani&subject=science&execute=true",
        auth=AUTH,
    )

    assert response.status_code == 200
    assert len(response.json()["published"]) == 1
    assert response.json()["published"][0]["commit_sha"].startswith("mock-")


def test_admin_publish_execute_requires_super_admin(monkeypatch) -> None:
    client = _client_with_seed_data(monkeypatch)
    monkeypatch.setenv("ADMIN_ROLE", "reviewer")
    get_settings.cache_clear()

    response = client.post(
        "/admin/publishing/batch?region=pattani&subject=science&execute=true",
        auth=AUTH,
    )

    assert response.status_code == 403


def test_admin_submission_review_flow(monkeypatch) -> None:
    client = _client_with_seed_data(monkeypatch)

    created = client.post(
        "/admin/submissions",
        auth=AUTH,
        json={
            "title": "Teacher market contribution",
            "subject": "math",
            "topic": "fractions",
            "grade_min": 4,
            "grade_max": 4,
            "content_en": "Use market sharing to teach fractions.",
            "submit": True,
        },
    )
    assert created.status_code == 200
    submission_id = created.json()["id"]
    assert created.json()["status"] == "pending_review"

    blocked = client.post(f"/admin/submissions/{submission_id}/publish-to-knowledge", auth=AUTH)
    assert blocked.status_code == 409

    first = client.post(
        f"/admin/submissions/{submission_id}/first-approve",
        auth=AUTH,
        json={"note": "Looks useful."},
    )
    assert first.status_code == 200
    assert first.json()["status"] == "first_approved"

    second = client.post(
        f"/admin/submissions/{submission_id}/second-approve",
        auth=AUTH,
        json={"note": "Approved for RAG."},
    )
    assert second.status_code == 200
    assert second.json()["status"] == "second_approved"

    published = client.post(f"/admin/submissions/{submission_id}/publish-to-knowledge", auth=AUTH)
    assert published.status_code == 200
    assert published.json()["status"] == "embedded"
    assert published.json()["knowledge_item_id"]

    detail = client.get(f"/admin/submissions/{submission_id}", auth=AUTH)
    assert detail.status_code == 200
    assert {review["action"] for review in detail.json()["reviews"]} >= {
        "submitted",
        "first_approved",
        "second_approved",
        "published",
        "embedded",
    }


def test_submission_delete_is_hidden_from_default_list(monkeypatch) -> None:
    client = _client_with_seed_data(monkeypatch)
    before = client.get("/admin/overview", auth=AUTH)
    created = client.post(
        "/admin/submissions",
        auth=AUTH,
        json={
            "title": "Delete me",
            "subject": "science",
            "topic": "weather",
            "grade_min": 4,
            "grade_max": 4,
            "content_en": "Temporary deleted test.",
            "submit": True,
        },
    )
    submission_id = created.json()["id"]
    after_create = client.get("/admin/overview", auth=AUTH)

    deleted = client.post(
        f"/admin/submissions/{submission_id}/delete",
        auth=AUTH,
        json={"note": "No longer needed."},
    )

    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"
    default_list = client.get("/admin/submissions", auth=AUTH)
    assert submission_id not in {item["id"] for item in default_list.json()["items"]}
    deleted_list = client.get("/admin/submissions?status=deleted", auth=AUTH)
    assert submission_id in {item["id"] for item in deleted_list.json()["items"]}
    detail = client.get(f"/admin/submissions/{submission_id}", auth=AUTH)
    assert detail.status_code == 200
    assert detail.json()["reviews"][-1]["action"] == "deleted"
    after_delete = client.get("/admin/overview", auth=AUTH)
    assert after_create.json()["counts"]["submissions"] == before.json()["counts"]["submissions"] + 1
    assert after_delete.json()["counts"]["submissions"] == before.json()["counts"]["submissions"]
    assert "deleted" not in after_delete.json()["submission_status"]


def test_school_admin_scope_filters_school_data(monkeypatch) -> None:
    client = _client_with_seed_data(monkeypatch)

    with admin.SessionLocal() as db:
        scoped_school = db.scalar(select(models.School).where(models.School.name == "Admin Test School"))
        other_school = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(
                name="Other School",
                region_code="narathiwat",
                region_name="Narathiwat",
            )
        )
        OnboardingService(db).bind_teacher_by_school_code(
            line_user_id="other-line-user",
            school_code=other_school.school_code,
        )
        other_request = LessonRequestService(db).create_from_teacher_text(
            line_user_id="other-line-user",
            text="Grade 4 science plants",
            enqueue=False,
        )
        other_lesson_id = other_request["lesson_request_id"]

    monkeypatch.setenv("ADMIN_ROLE", "school_admin")
    monkeypatch.setenv("ADMIN_SCHOOL_IDS", str(scoped_school.id))
    get_settings.cache_clear()

    me = client.get("/admin/me", auth=AUTH)
    assert me.status_code == 200
    assert me.json()["role"] == "school_admin"
    assert me.json()["school_ids"] == [str(scoped_school.id)]

    schools = client.get("/admin/schools", auth=AUTH)
    assert schools.status_code == 200
    assert [item["name"] for item in schools.json()["items"]] == ["Admin Test School"]

    teachers = client.get("/admin/teachers", auth=AUTH)
    assert teachers.status_code == 200
    assert {item["line_user_id"] for item in teachers.json()["items"]} == {"admin-line-user"}

    lessons = client.get("/admin/lessons", auth=AUTH)
    assert lessons.status_code == 200
    assert {item["school_id"] for item in lessons.json()["items"]} == {str(scoped_school.id)}

    blocked_lesson = client.get(f"/admin/lessons/{other_lesson_id}", auth=AUTH)
    assert blocked_lesson.status_code == 403

    publishing = client.get("/admin/publishing/candidates?region=pattani", auth=AUTH)
    assert publishing.status_code == 403


def test_school_admin_submission_and_knowledge_are_school_private(monkeypatch) -> None:
    client = _client_with_seed_data(monkeypatch)

    with admin.SessionLocal() as db:
        scoped_school = db.scalar(select(models.School).where(models.School.name == "Admin Test School"))

    monkeypatch.setenv("ADMIN_ROLE", "school_admin")
    monkeypatch.setenv("ADMIN_SCHOOL_IDS", str(scoped_school.id))
    get_settings.cache_clear()

    created = client.post(
        "/admin/submissions",
        auth=AUTH,
        json={
            "title": "School private contribution",
            "subject": "science",
            "topic": "rain",
            "grade_min": 4,
            "grade_max": 4,
            "visibility_scope": "shared_region",
            "content_en": "School-only rain example.",
            "submit": True,
        },
    )

    assert created.status_code == 200
    assert created.json()["school_id"] == str(scoped_school.id)
    assert created.json()["visibility_scope"] == "private_school"

    imported = client.post(
        "/admin/knowledge/seed",
        auth=AUTH,
        json={
            "knowledge_type": "local_example",
            "title": "School private knowledge",
            "visibility_scope": "shared_region",
            "subject": "science",
            "topic": "rain",
            "target_grade": 4,
            "grade_min": 4,
            "grade_max": 4,
            "content_en": "School-only knowledge.",
            "verified": True,
        },
    )
    assert imported.status_code == 200

    knowledge = client.get("/admin/knowledge", auth=AUTH)
    assert knowledge.status_code == 200
    private_item = next(
        item for item in knowledge.json()["items"] if item["title"] == "School private knowledge"
    )
    assert private_item["visibility_scope"] == "private_school"
    assert private_item["review_status"] == "pending_review"

    blocked_region_approval = client.post(
        f"/admin/knowledge/{private_item['id']}/approve-region-shared",
        auth=AUTH,
    )
    assert blocked_region_approval.status_code == 403


def test_school_admin_publish_shared_submission_creates_private_knowledge(monkeypatch) -> None:
    client = _client_with_seed_data(monkeypatch)

    with admin.SessionLocal() as db:
        scoped_school = db.scalar(select(models.School).where(models.School.name == "Admin Test School"))
        submission = models.Submission(
            school_id=scoped_school.id,
            region_id=scoped_school.region_id,
            status="second_approved",
            current_review_stage=2,
            visibility_scope="shared_region",
            knowledge_type="local_example",
            subject="science",
            topic="rain",
            title="Teacher shared contribution",
            target_grade=4,
            grade_min=4,
            grade_max=4,
            content_en="A rain example submitted by a teacher.",
            source_note="LINE teacher submission.",
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
        submission_id = str(submission.id)

    monkeypatch.setenv("ADMIN_ROLE", "school_admin")
    monkeypatch.setenv("ADMIN_SCHOOL_IDS", str(scoped_school.id))
    get_settings.cache_clear()

    published = client.post(f"/admin/submissions/{submission_id}/publish-to-knowledge", auth=AUTH)

    assert published.status_code == 200
    assert published.json()["status"] == "embedded"
    assert published.json()["visibility_scope"] == "private_school"
    knowledge_item_id = published.json()["knowledge_item_id"]
    assert knowledge_item_id

    knowledge = client.get("/admin/knowledge", auth=AUTH)
    assert knowledge.status_code == 200
    item = next(item for item in knowledge.json()["items"] if item["id"] == knowledge_item_id)
    assert item["title"] == "Teacher shared contribution"
    assert item["visibility_scope"] == "private_school"
    assert item["owner_school_id"] == str(scoped_school.id)


def test_database_admin_users_login_with_separate_school_scopes(monkeypatch) -> None:
    client = _client_with_seed_data(monkeypatch)

    with admin.SessionLocal() as db:
        school_a = db.scalar(select(models.School).where(models.School.name == "Admin Test School"))
        school_b_result = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(
                name="Second Scoped School",
                region_code="yala",
                region_name="Yala",
            )
        )
        school_b = db.get(models.School, UUID(school_b_result.school_id))

    account_a = ("school-a@example.com", "school-a-pass")
    account_b = ("school-b@example.com", "school-b-pass")
    created_a = client.post(
        "/admin/users",
        auth=AUTH,
        json={
            "email": account_a[0],
            "password": account_a[1],
            "role": "school_admin",
            "school_ids": [str(school_a.id)],
            "region_ids": [],
            "active": True,
        },
    )
    created_b = client.post(
        "/admin/users",
        auth=AUTH,
        json={
            "email": account_b[0],
            "password": account_b[1],
            "role": "school_admin",
            "school_ids": [str(school_b.id)],
            "region_ids": [],
            "active": True,
        },
    )
    assert created_a.status_code == 200
    assert created_b.status_code == 200

    me_a = client.get("/admin/me", auth=account_a)
    assert me_a.status_code == 200
    assert me_a.json()["role"] == "school_admin"
    assert me_a.json()["school_ids"] == [str(school_a.id)]

    schools_a = client.get("/admin/schools", auth=account_a)
    schools_b = client.get("/admin/schools", auth=account_b)
    assert [item["id"] for item in schools_a.json()["items"]] == [str(school_a.id)]
    assert [item["id"] for item in schools_b.json()["items"]] == [str(school_b.id)]

    blocked_users = client.get("/admin/users", auth=account_a)
    assert blocked_users.status_code == 403

    blocked_publish = client.get("/admin/publishing/candidates", auth=account_a)
    assert blocked_publish.status_code == 403

    disabled = client.patch(
        f"/admin/users/{created_a.json()['id']}",
        auth=AUTH,
        json={"active": False},
    )
    assert disabled.status_code == 200
    assert client.get("/admin/me", auth=account_a).status_code == 401
