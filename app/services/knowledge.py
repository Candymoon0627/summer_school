from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.knowledge import KnowledgeChunk, KnowledgeItem
from app.repositories.audit import AuditRepository
from app.repositories.knowledge import KnowledgeRepository
from app.repositories.org import OrgRepository
from app.schemas.knowledge import KnowledgeSeedItem
from app.services.model_registry import get_embedding_provider

SNAPSHOT_FIELDS = [
    "owner_type",
    "owner_school_id",
    "owner_region_id",
    "visibility_scope",
    "review_status",
    "knowledge_type",
    "subject",
    "topic",
    "title",
    "target_grade",
    "grade_min",
    "grade_max",
    "grade_mode",
    "curriculum_codes",
    "curriculum_notes",
    "adaptation_notes",
    "content_th",
    "content_ms",
    "content_en",
    "type_specific",
    "local_context",
    "classroom_use",
    "materials_needed",
    "safety_notes",
    "sensitive_tags",
    "copyright_status",
    "quality_score",
    "source_type",
    "source_confidence",
    "source_note",
]


class KnowledgeService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.knowledge = KnowledgeRepository(db)
        self.orgs = OrgRepository(db)
        self.audit = AuditRepository(db)

    def import_seed_item(self, seed: KnowledgeSeedItem) -> KnowledgeItem:
        region = None
        school = self.orgs.get_school_by_id(UUID(seed.owner_school_id)) if seed.owner_school_id else None
        if school:
            region_id = school.region_id
            owner_school_id = school.id
            owner_type = "school"
        elif seed.region_code:
            region = self.orgs.get_or_create_region(
                code=seed.region_code,
                name=seed.region_code.title(),
                country_code="th",
            )
            region_id = region.id
            owner_school_id = None
            owner_type = "project"
        else:
            region_id = None
            owner_school_id = None
            owner_type = "project"
        review_status = "approved_region_shared" if seed.verified else "pending_review"
        if seed.visibility_scope == "private_school":
            review_status = "approved_school_private" if seed.verified else "pending_review"
        item = self.knowledge.create_item(
            owner_type=owner_type,
            owner_school_id=owner_school_id,
            owner_region_id=region_id,
            visibility_scope=seed.visibility_scope,
            review_status=review_status,
            knowledge_type=seed.knowledge_type,
            subject=seed.subject,
            topic=seed.topic,
            title=seed.title,
            target_grade=seed.target_grade,
            grade_min=seed.grade_min,
            grade_max=seed.grade_max,
            grade_mode=seed.grade_mode,
            content_th=seed.content_th,
            content_ms=seed.content_ms,
            content_en=seed.content_en,
            local_context=seed.local_context,
            classroom_use=seed.classroom_use,
            safety_notes=seed.safety_notes,
            quality_score=seed.quality_score,
            source_type=seed.source_type,
            source_confidence=seed.source_confidence,
            source_note=seed.source_note,
            copyright_status="likely_original",
            vector_status="not_embedded",
        )
        self.create_version(item, "created", "Imported seed knowledge.")
        if review_status.startswith("approved"):
            self.rebuild_chunks_and_embedding(item.id)
        self.db.commit()
        return item

    def create_version(
        self,
        item: KnowledgeItem,
        change_type: str,
        change_summary: str | None = None,
    ) -> None:
        self.knowledge.create_version(
            item=item,
            snapshot=self.snapshot(item),
            change_type=change_type,
            change_summary=change_summary,
        )

    def snapshot(self, item: KnowledgeItem) -> dict:
        data = {}
        for field in SNAPSHOT_FIELDS:
            value = getattr(item, field)
            data[field] = str(value) if field.endswith("_id") and value is not None else value
        return data

    def rebuild_chunks_and_embedding(
        self,
        item_id: UUID | str,
        *,
        commit: bool = True,
    ) -> list[KnowledgeChunk]:
        from uuid import UUID as UUIDType

        if isinstance(item_id, str):
            item_id = UUIDType(item_id)
        item = self.knowledge.get_item(item_id)
        if not item:
            raise ValueError(f"Knowledge item not found: {item_id}")

        provider = get_embedding_provider()
        chunk_text = self.render_chunk_text(item)
        embedding = provider.embed(chunk_text)
        chunk = KnowledgeChunk(
            knowledge_item_id=item.id,
            chunk_index=0,
            chunk_text=chunk_text,
            language="mixed",
            region_id=item.owner_region_id,
            school_id=item.owner_school_id,
            subject=item.subject,
            topic=item.topic,
            grade_min=item.grade_min,
            grade_max=item.grade_max,
            embedding_provider=getattr(provider, "provider_name", "unknown"),
            embedding_model=getattr(provider, "model_name", "unknown"),
            embedding_dimensions=len(embedding),
            embedding_json=embedding,
            active=True,
        )
        self.knowledge.replace_chunks(item, [chunk])
        item.vector_status = "embedded"
        if commit:
            self.db.commit()
        return [chunk]

    def approve_school_private(
        self,
        item_id: UUID | str,
        *,
        actor_admin_id: UUID | None = None,
    ) -> KnowledgeItem:
        item = self._get_item_or_raise(item_id)
        before = self.snapshot(item)
        item.visibility_scope = "private_school"
        item.review_status = "approved_school_private"
        self.create_version(item, "reviewed", "Approved for school private RAG.")
        self.rebuild_chunks_and_embedding(item.id, commit=False)
        self.audit.create(
            actor_admin_id=actor_admin_id,
            action="knowledge_approved_school_private",
            target_type="knowledge_item",
            target_id=str(item.id),
            before_snapshot=before,
            after_snapshot=self.snapshot(item),
        )
        self.db.commit()
        return item

    def approve_region_shared(
        self,
        item_id: UUID | str,
        *,
        actor_admin_id: UUID | None = None,
    ) -> KnowledgeItem:
        item = self._get_item_or_raise(item_id)
        before = self.snapshot(item)
        item.visibility_scope = "shared_region"
        item.review_status = "approved_region_shared"
        self.create_version(item, "reviewed", "Approved for regional shared RAG.")
        self.rebuild_chunks_and_embedding(item.id, commit=False)
        self.audit.create(
            actor_admin_id=actor_admin_id,
            action="knowledge_approved_region_shared",
            target_type="knowledge_item",
            target_id=str(item.id),
            before_snapshot=before,
            after_snapshot=self.snapshot(item),
        )
        self.db.commit()
        return item

    def soft_delete(
        self,
        item_id: UUID | str,
        reason: str | None = None,
        *,
        actor_admin_id: UUID | None = None,
    ) -> KnowledgeItem:
        item = self._get_item_or_raise(item_id)
        before = self.snapshot(item)
        item.is_deleted = True
        item.review_status = "archived"
        item.vector_status = "needs_reembed"
        self.create_version(item, "deleted", reason or "Soft deleted.")
        for chunk in self.knowledge.chunks_for_item(item.id):
            chunk.active = False
        self.audit.create(
            actor_admin_id=actor_admin_id,
            action="knowledge_soft_deleted",
            target_type="knowledge_item",
            target_id=str(item.id),
            before_snapshot=before,
            after_snapshot=self.snapshot(item) | {"is_deleted": item.is_deleted},
        )
        self.db.commit()
        return item

    def restore_version(
        self,
        item_id: UUID | str,
        version_number: int,
        *,
        actor_admin_id: UUID | None = None,
    ) -> KnowledgeItem:
        item = self._get_item_or_raise(item_id)
        before = self.snapshot(item)
        version = self.knowledge.get_version(item.id, version_number)
        if not version:
            raise ValueError(f"Version {version_number} not found for knowledge item {item.id}")
        snapshot = version.snapshot
        for field, value in snapshot.items():
            if field.endswith("_id") and value is not None:
                value = UUID(value)
            setattr(item, field, value)
        item.vector_status = "needs_reembed"
        if item.visibility_scope in {"shared_region", "shared_global"}:
            item.review_status = "pending_republish"
        self.create_version(item, "restored", f"Restored version {version_number}.")
        self.audit.create(
            actor_admin_id=actor_admin_id,
            action="knowledge_version_restored",
            target_type="knowledge_item",
            target_id=str(item.id),
            before_snapshot=before,
            after_snapshot=self.snapshot(item),
        )
        self.db.commit()
        return item

    def reject(
        self,
        item_id: UUID | str,
        reason: str | None = None,
        *,
        actor_admin_id: UUID | None = None,
    ) -> KnowledgeItem:
        item = self._get_item_or_raise(item_id)
        before = self.snapshot(item)
        item.review_status = "rejected"
        item.vector_status = "not_embedded"
        self.create_version(item, "rejected", reason or "Rejected.")
        self.audit.create(
            actor_admin_id=actor_admin_id,
            action="knowledge_rejected",
            target_type="knowledge_item",
            target_id=str(item.id),
            before_snapshot=before,
            after_snapshot=self.snapshot(item),
        )
        self.db.commit()
        return item

    def _get_item_or_raise(self, item_id: UUID | str) -> KnowledgeItem:
        from uuid import UUID as UUIDType

        if isinstance(item_id, str):
            item_id = UUIDType(item_id)
        item = self.knowledge.get_item(item_id)
        if not item:
            raise ValueError(f"Knowledge item not found: {item_id}")
        return item

    def render_chunk_text(self, item: KnowledgeItem) -> str:
        return f"""Knowledge type: {item.knowledge_type}
Region ID: {item.owner_region_id or "global"}
Subject: {item.subject}
Grade: {item.grade_min}-{item.grade_max}
Topic: {item.topic}
Title: {item.title}

Thai:
{item.content_th or ""}

Local Malay Helper:
{item.content_ms or ""}

English:
{item.content_en or ""}

Local Context:
{item.local_context or ""}

Classroom Use:
{item.classroom_use or ""}

Safety Notes:
{item.safety_notes or ""}
"""
