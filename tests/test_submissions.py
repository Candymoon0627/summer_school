from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.admin_auth import AdminPrincipal
from app.db import models
from app.db.base import Base
from app.schemas.admin import CreateSchoolRequest
from app.schemas.submission import SubmissionCreate
from app.services.onboarding import OnboardingService
from app.services.submissions import SubmissionService


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def test_submission_requires_two_reviews_before_publish() -> None:
    Session = _session()
    admin = AdminPrincipal(username="reviewer", role="reviewer")

    with Session() as db:
        service = SubmissionService(db)
        submission = service.create_admin_submission(
            SubmissionCreate(
                title="Local fractions example",
                subject="math",
                topic="fractions",
                grade_min=4,
                grade_max=4,
                content_en="Use a market sharing example to teach fractions.",
                submit=True,
            ),
            current_admin=admin,
        )

        try:
            service.publish_to_knowledge(submission.id, current_admin=admin)
        except ValueError as exc:
            assert "second_approved" in str(exc)
        else:
            raise AssertionError("Publishing before second review should fail.")

        service.first_approve(submission.id, current_admin=admin)
        service.second_approve(submission.id, current_admin=admin)
        published = service.publish_to_knowledge(submission.id, current_admin=admin)

        assert published.status == "embedded"
        assert published.knowledge_item_id is not None
        knowledge = db.get(models.KnowledgeItem, published.knowledge_item_id)
        assert knowledge is not None
        assert knowledge.review_status == "approved_region_shared"
        chunks = db.query(models.KnowledgeChunk).filter_by(knowledge_item_id=knowledge.id, active=True).all()
        assert len(chunks) == 1


def test_line_text_submission_uses_bound_teacher_context() -> None:
    Session = _session()

    with Session() as db:
        school = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(name="Submission School", region_code="pattani", region_name="Pattani")
        )
        OnboardingService(db).bind_teacher_by_school_code(
            line_user_id="line-submitter",
            school_code=school.school_code,
        )

        submission = SubmissionService(db).create_line_text_submission(
            line_user_id="line-submitter",
            text="投稿：Use fishing boats to explain distance and time.",
            source_message_id="line-message-1",
        )

        assert submission.status == "pending_review"
        assert submission.school_id is not None
        assert submission.region_id is not None
        assert submission.source_type == "line_text"
        assert submission.content_th == "Use fishing boats to explain distance and time."


def test_line_text_submission_classifies_grade_subject_and_topic() -> None:
    Session = _session()

    with Session() as db:
        school = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(name="Classified Submission School", region_code="pattani", region_name="Pattani")
        )
        OnboardingService(db).bind_teacher_by_school_code(
            line_user_id="line-classified-submitter",
            school_code=school.school_code,
        )

        submission = SubmissionService(db).create_line_text_submission(
            line_user_id="line-classified-submitter",
            text=(
                "submit: Grade 4 fractions activity using a local market example. "
                "Students compare 1/2, 1/3, and 1/4."
            ),
            source_message_id="line-message-classified-1",
        )

        assert submission.subject == "math"
        assert submission.topic == "fractions"
        assert submission.target_grade == 4
        assert submission.grade_min == 4
        assert submission.grade_max == 4
