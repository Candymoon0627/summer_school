from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.audit import AuditRepository
from app.repositories.knowledge import KnowledgeRepository
from app.services.safety import SafetyService


class ContentReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.knowledge = KnowledgeRepository(db)
        self.audit = AuditRepository(db)
        self.safety = SafetyService()

    def run_sensitive_check(self, item_id: UUID | str) -> dict:
        item = self._get_item(item_id)
        text = self._item_text(item)
        result = self.safety.classify_sensitive_content(text)
        item.sensitive_tags = result.get("tags", [])
        risk_level = result.get("risk_level", "low")
        if risk_level in {"high", "blocked"}:
            item.review_status = "sensitive_hold"
        self.audit.create(
            action="knowledge_sensitive_checked",
            target_type="knowledge_item",
            target_id=str(item.id),
            after_snapshot={"risk_level": risk_level, "tags": item.sensitive_tags},
        )
        self.db.commit()
        return {"risk_level": risk_level, "tags": item.sensitive_tags}

    def run_copyright_check(self, item_id: UUID | str) -> dict:
        item = self._get_item(item_id)
        text = self._item_text(item)
        result = self.safety.classify_copyright_risk(text)
        status = result.get("copyright_status") or result.get("status") or "likely_original"
        item.copyright_status = status
        self.audit.create(
            action="knowledge_copyright_checked",
            target_type="knowledge_item",
            target_id=str(item.id),
            after_snapshot={"copyright_status": item.copyright_status, "result": result},
        )
        self.db.commit()
        return {"copyright_status": item.copyright_status, "result": result}

    def _get_item(self, item_id: UUID | str):
        from uuid import UUID as UUIDType

        if isinstance(item_id, str):
            item_id = UUIDType(item_id)
        item = self.knowledge.get_item(item_id)
        if not item:
            raise ValueError(f"Knowledge item not found: {item_id}")
        return item

    def _item_text(self, item) -> str:
        return "\n".join(
            part
            for part in [
                item.title,
                item.content_th,
                item.content_ms,
                item.content_en,
                item.local_context,
                item.classroom_use,
                item.safety_notes,
            ]
            if part
        )

