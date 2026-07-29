from collections import defaultdict

from sqlalchemy.orm import Session

from app.repositories.knowledge import KnowledgeRepository


class CoverageService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.knowledge = KnowledgeRepository(db)

    def knowledge_coverage(self, limit: int = 1000) -> list[dict]:
        buckets: dict[tuple, dict] = defaultdict(
            lambda: {
                "knowledge_count": 0,
                "high_quality_count": 0,
                "embedded_count": 0,
            }
        )
        for item in self.knowledge.list_items(limit=limit):
            key = (
                str(item.owner_region_id) if item.owner_region_id else "global",
                item.subject,
                item.target_grade or f"{item.grade_min}-{item.grade_max}",
                item.topic,
                item.knowledge_type,
                item.visibility_scope,
            )
            bucket = buckets[key]
            bucket["region_id"], bucket["subject"], bucket["grade"], bucket["topic"], bucket[
                "knowledge_type"
            ], bucket["visibility_scope"] = key
            bucket["knowledge_count"] += 1
            if item.quality_score >= 4:
                bucket["high_quality_count"] += 1
            if item.vector_status == "embedded":
                bucket["embedded_count"] += 1
        return sorted(
            buckets.values(),
            key=lambda item: (item["knowledge_count"], item["high_quality_count"]),
            reverse=True,
        )
