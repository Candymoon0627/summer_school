from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db.models.lesson import LessonKnowledgeRef, LessonRequest


class LessonRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_lesson_request(
        self,
        *,
        teacher_id: UUID,
        school_id: UUID,
        region_id: UUID,
        raw_user_input: str,
        subject: str | None,
        grade: int | None,
        topic: str | None,
    ) -> LessonRequest:
        lesson_request = LessonRequest(
            teacher_id=teacher_id,
            school_id=school_id,
            region_id=region_id,
            raw_user_input=raw_user_input,
            subject=subject,
            grade=grade,
            topic=topic,
            status="queued",
        )
        self.db.add(lesson_request)
        self.db.flush()
        return lesson_request

    def recent_for_teacher(self, teacher_id: UUID, limit: int = 5) -> list[LessonRequest]:
        return list(
            self.db.scalars(
                select(LessonRequest)
                .where(LessonRequest.teacher_id == teacher_id)
                .order_by(LessonRequest.created_at.desc())
                .limit(limit)
            )
        )

    def list_requests(
        self,
        *,
        limit: int = 100,
        status: str | None = None,
        teacher_id: UUID | None = None,
    ) -> list[LessonRequest]:
        statement = select(LessonRequest).order_by(LessonRequest.created_at.desc()).limit(limit)
        if status:
            statement = statement.where(LessonRequest.status == status)
        if teacher_id:
            statement = statement.where(LessonRequest.teacher_id == teacher_id)
        return list(self.db.scalars(statement))

    def get_request(self, lesson_request_id: UUID) -> LessonRequest | None:
        return self.db.get(LessonRequest, lesson_request_id)

    def knowledge_refs_for_request(self, lesson_request_id: UUID) -> list[LessonKnowledgeRef]:
        return list(
            self.db.scalars(
                select(LessonKnowledgeRef)
                .where(LessonKnowledgeRef.lesson_request_id == lesson_request_id)
                .order_by(LessonKnowledgeRef.rank.asc())
            )
        )

    def status_counts(self) -> dict[str, int]:
        rows = self.db.execute(
            select(LessonRequest.status, func.count()).group_by(LessonRequest.status)
        ).all()
        return {status: count for status, count in rows}

    def replace_knowledge_refs(
        self,
        lesson_request_id: UUID,
        retrieved: list,
    ) -> list[LessonKnowledgeRef]:
        self.db.execute(
            delete(LessonKnowledgeRef).where(LessonKnowledgeRef.lesson_request_id == lesson_request_id)
        )
        refs = []
        for rank, item in enumerate(retrieved, start=1):
            ref = LessonKnowledgeRef(
                lesson_request_id=lesson_request_id,
                knowledge_item_id=UUID(item.knowledge_item_id),
                knowledge_item_version_id=UUID(item.knowledge_item_version_id)
                if item.knowledge_item_version_id
                else None,
                chunk_id=UUID(item.chunk_id) if item.chunk_id else None,
                relevance_score=item.score,
                rank=rank,
                used_in_section="rag_prompt",
            )
            self.db.add(ref)
            refs.append(ref)
        self.db.flush()
        return refs
