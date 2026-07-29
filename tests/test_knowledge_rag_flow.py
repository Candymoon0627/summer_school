from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models.lesson import LessonKnowledgeRef
from app.schemas.admin import CreateSchoolRequest
from app.schemas.knowledge import KnowledgeSeedItem
from app.services.knowledge import KnowledgeService
from app.services.lesson_generation import LessonGenerationService
from app.services.lesson_requests import LessonRequestService
from app.services.onboarding import OnboardingService
from app.services.rag import RagService


def test_seed_knowledge_becomes_searchable_for_same_region_teacher() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    with Session() as db:
        school = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(name="Test School", region_code="pattani", region_name="Pattani")
        )
        teacher = OnboardingService(db).bind_teacher_by_school_code(
            line_user_id="line-user-rag",
            school_code=school.school_code,
        )
        assert teacher is not None

        item = KnowledgeService(db).import_seed_item(
            KnowledgeSeedItem(
                knowledge_type="local_example",
                title="Fish sharing for fractions",
                region_code="pattani",
                visibility_scope="shared_region",
                subject="math",
                topic="fractions",
                target_grade=4,
                grade_min=3,
                grade_max=5,
                content_en="Use fish sharing at a local market to explain fractions.",
                local_context="Pattani market sharing example.",
                classroom_use="Students divide 8 fish among 4 families.",
                verified=True,
            )
        )
        assert item.vector_status == "embedded"

        results, confidence = RagService(db).retrieve_for_lesson(
            teacher_id=str(teacher.teacher_id),
            school_id=str(teacher.school_id),
            region_id=str(teacher.region_id),
            subject="math",
            grade=4,
            topic="fractions",
        )
        assert confidence in {"medium", "high"}
        assert results
        assert results[0].title == "Fish sharing for fractions"

        request = LessonRequestService(db).create_from_teacher_text(
            line_user_id="line-user-rag",
            text="Grade 4 math fractions",
            enqueue=False,
        )
        lesson = LessonGenerationService(db).generate(request["lesson_request_id"])
        refs = list(
            db.scalars(
                select(LessonKnowledgeRef).where(
                    LessonKnowledgeRef.lesson_request_id == lesson.id
                )
            )
        )
        assert refs
        assert refs[0].knowledge_item_id == item.id
        assert refs[0].used_in_section == "rag_prompt"
        assert lesson.model_provider == "mock"
        assert lesson.model_name == "mock-lesson-v1"


def test_knowledge_soft_delete_removes_from_rag() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    with Session() as db:
        school = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(name="Test School", region_code="pattani", region_name="Pattani")
        )
        teacher = OnboardingService(db).bind_teacher_by_school_code(
            line_user_id="line-user-delete",
            school_code=school.school_code,
        )
        assert teacher is not None
        item = KnowledgeService(db).import_seed_item(
            KnowledgeSeedItem(
                knowledge_type="local_example",
                title="Market measurement",
                region_code="pattani",
                visibility_scope="shared_region",
                subject="math",
                topic="measurement",
                target_grade=4,
                grade_min=4,
                grade_max=4,
                content_en="Use market weighing to teach measurement.",
                verified=True,
            )
        )

        KnowledgeService(db).soft_delete(item.id, "test delete")
        results, confidence = RagService(db).retrieve_for_lesson(
            teacher_id=str(teacher.teacher_id),
            school_id=str(teacher.school_id),
            region_id=str(teacher.region_id),
            subject="math",
            grade=4,
            topic="measurement",
        )
        assert confidence == "low"
        assert results == []
