from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.knowledge import KnowledgeItem
from app.db.models.org import Region
from app.services.publishing import GitHubPublishingService, PublishResult

PUBLISHABLE_STATUSES = {"approved_region_shared", "approved_global_shared", "pending_republish"}
PUBLISHABLE_SCOPES = {"shared_region", "shared_global"}


@dataclass(frozen=True)
class PublishCandidate:
    id: str
    title: str
    subject: str
    topic: str
    visibility_scope: str
    review_status: str
    source_type: str
    source_confidence: str
    github_path: str | None
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BatchPublishResult:
    candidates: list[PublishCandidate]
    published: list[PublishResult] = field(default_factory=list)


class KnowledgeBatchPublishingService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def candidates(
        self,
        *,
        region_code: str | None = None,
        subject: str | None = None,
        allow_test_data: bool = False,
        limit: int = 100,
    ) -> list[PublishCandidate]:
        statement = (
            select(KnowledgeItem)
            .outerjoin(Region, Region.id == KnowledgeItem.owner_region_id)
            .where(
                KnowledgeItem.is_deleted.is_(False),
                KnowledgeItem.visibility_scope.in_(PUBLISHABLE_SCOPES),
                KnowledgeItem.review_status.in_(PUBLISHABLE_STATUSES),
            )
            .order_by(KnowledgeItem.created_at.asc())
            .limit(limit)
        )
        if region_code:
            statement = statement.where(Region.code == region_code)
        if subject:
            statement = statement.where(KnowledgeItem.subject == subject)
        if not allow_test_data:
            statement = statement.where(KnowledgeItem.source_type != "oer_synthetic_test")

        renderer = GitHubPublishingService(self.db).renderer
        items = list(self.db.scalars(statement))
        return [
            PublishCandidate(
                id=str(item.id),
                title=item.title,
                subject=item.subject,
                topic=item.topic,
                visibility_scope=item.visibility_scope,
                review_status=item.review_status,
                source_type=item.source_type,
                source_confidence=item.source_confidence,
                github_path=renderer.path_for(item),
                warnings=self._warnings(item),
            )
            for item in items
        ]

    def publish(
        self,
        *,
        region_code: str | None = None,
        subject: str | None = None,
        allow_test_data: bool = False,
        allow_warnings: bool = False,
        limit: int = 100,
        dry_run: bool = True,
    ) -> BatchPublishResult:
        candidates = self.candidates(
            region_code=region_code,
            subject=subject,
            allow_test_data=allow_test_data,
            limit=limit,
        )
        if dry_run:
            return BatchPublishResult(candidates=candidates)
        if not allow_warnings:
            blocked = [candidate for candidate in candidates if candidate.warnings]
            if blocked:
                ids = ", ".join(candidate.id for candidate in blocked[:5])
                raise ValueError(
                    "Refusing to publish candidates with warnings. "
                    f"First blocked ids: {ids}. Pass allow_warnings=True to override."
                )

        publisher = GitHubPublishingService(self.db)
        published = [publisher.publish_knowledge_item(candidate.id) for candidate in candidates]
        return BatchPublishResult(candidates=candidates, published=published)

    def _warnings(self, item: KnowledgeItem) -> list[str]:
        warnings = []
        if not item.content_th:
            warnings.append("missing_content_th")
        if not item.content_ms:
            warnings.append("missing_content_ms")
        if not item.content_en:
            warnings.append("missing_content_en")
        if not item.source_note:
            warnings.append("missing_source_note")
        if item.source_type == "oer_synthetic_test":
            warnings.append("test_data")
        return warnings
