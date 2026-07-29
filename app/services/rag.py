import math
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.models.knowledge import KnowledgeChunk
from app.repositories.knowledge import KnowledgeRepository
from app.services.model_registry import get_embedding_provider


@dataclass(frozen=True)
class RetrievedKnowledge:
    knowledge_item_id: str
    knowledge_item_version_id: str | None
    chunk_id: str | None
    title: str
    content: str
    score: float


class RagService:
    strategy_version = "filtered_vector_light_rerank_v1"

    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    def retrieve_for_lesson(
        self,
        *,
        teacher_id: str,
        school_id: str,
        region_id: str,
        subject: str,
        grade: int,
        topic: str,
    ) -> tuple[list[RetrievedKnowledge], str]:
        if self.db is None:
            return [], "low"

        from uuid import UUID

        del teacher_id
        query_embedding = get_embedding_provider().embed(f"{subject} {grade} {topic}")
        chunks = KnowledgeRepository(self.db).search_allowed_chunks(
            school_id=UUID(school_id),
            region_id=UUID(region_id),
            subject=subject,
            grade=grade,
            topic=topic,
            limit=30,
        )
        ranked = sorted(
            (self._score_chunk(chunk, query_embedding, topic, grade) for chunk in chunks),
            key=lambda item: item[0],
            reverse=True,
        )
        results = [
            RetrievedKnowledge(
                knowledge_item_id=str(chunk.knowledge_item_id),
                knowledge_item_version_id=self._latest_version_id(chunk),
                chunk_id=str(chunk.id),
                title=self._chunk_title(chunk),
                content=chunk.chunk_text,
                score=score,
            )
            for score, chunk in ranked[:8]
        ]
        confidence = self._confidence(results)
        return results, confidence

    def _score_chunk(
        self,
        chunk: KnowledgeChunk,
        query_embedding: list[float],
        topic: str,
        grade: int,
    ) -> tuple[float, KnowledgeChunk]:
        vector_score = cosine_similarity(query_embedding, chunk.embedding_json or [])
        topic_boost = 0.1 if topic.lower() in (chunk.topic or "").lower() else 0
        grade_boost = 0.05 if chunk.grade_min <= grade <= chunk.grade_max else 0
        return vector_score + topic_boost + grade_boost, chunk

    def _chunk_title(self, chunk: KnowledgeChunk) -> str:
        for line in chunk.chunk_text.splitlines():
            if line.startswith("Title:"):
                return line.replace("Title:", "").strip()
        return "Local knowledge"

    def _latest_version_id(self, chunk: KnowledgeChunk) -> str | None:
        if self.db is None:
            return None
        version = KnowledgeRepository(self.db).latest_version(chunk.knowledge_item_id)
        return str(version.id) if version else None

    def _confidence(self, results: list[RetrievedKnowledge]) -> str:
        if len(results) >= 3 and results[0].score >= 0.55:
            return "high"
        if len(results) >= 1:
            return "medium"
        return "low"


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
