from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.duplicate import DuplicateRepository
from app.repositories.knowledge import KnowledgeRepository
from app.services.rag import cosine_similarity


class DuplicateDetectionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.knowledge = KnowledgeRepository(db)
        self.duplicates = DuplicateRepository(db)

    def detect_for_item(self, item_id: UUID | str, threshold: float = 0.82) -> list[dict]:
        from uuid import UUID as UUIDType

        if isinstance(item_id, str):
            item_id = UUIDType(item_id)
        item_chunks = [chunk for chunk in self.knowledge.chunks_for_item(item_id) if chunk.active]
        if not item_chunks:
            return []
        base_chunk = item_chunks[0]
        candidates: list[dict] = []
        for chunk in self.knowledge.active_chunks():
            if chunk.knowledge_item_id == item_id:
                continue
            score = cosine_similarity(base_chunk.embedding_json or [], chunk.embedding_json or [])
            if score >= threshold:
                self.duplicates.create_candidate(
                    knowledge_item_id=item_id,
                    candidate_item_id=chunk.knowledge_item_id,
                    similarity_score=score,
                )
                candidates.append(
                    {
                        "candidate_item_id": str(chunk.knowledge_item_id),
                        "similarity_score": score,
                    }
                )
        self.db.commit()
        return sorted(candidates, key=lambda item: item["similarity_score"], reverse=True)

    def merge_duplicate(self, *, duplicate_item_id: UUID | str, main_item_id: UUID | str) -> dict:
        from uuid import UUID as UUIDType

        if isinstance(duplicate_item_id, str):
            duplicate_item_id = UUIDType(duplicate_item_id)
        if isinstance(main_item_id, str):
            main_item_id = UUIDType(main_item_id)
        duplicate = self.knowledge.get_item(duplicate_item_id)
        main = self.knowledge.get_item(main_item_id)
        if not duplicate or not main:
            raise ValueError("Both duplicate and main knowledge items must exist.")
        duplicate.review_status = "merged"
        duplicate.is_deleted = True
        duplicate.type_specific = {
            **(duplicate.type_specific or {}),
            "merged_into_knowledge_item_id": str(main.id),
        }
        for chunk in self.knowledge.chunks_for_item(duplicate.id):
            chunk.active = False
        self.db.commit()
        return {"status": "merged", "duplicate_item_id": str(duplicate.id), "main_item_id": str(main.id)}

