import hashlib
from dataclasses import dataclass

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.repositories.audit import AuditRepository
from app.repositories.knowledge import KnowledgeRepository
from app.services.markdown import KnowledgeMarkdownRenderer, KnowledgeMarkdownValidator


@dataclass(frozen=True)
class PublishResult:
    github_path: str
    commit_sha: str


class GitHubPublishingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.knowledge = KnowledgeRepository(db)
        self.audit = AuditRepository(db)
        self.renderer = KnowledgeMarkdownRenderer()
        self.validator = KnowledgeMarkdownValidator()

    def publish_knowledge_item(self, knowledge_item_id: str) -> PublishResult:
        from uuid import UUID

        item = self.knowledge.get_item(UUID(knowledge_item_id))
        if not item:
            raise ValueError(f"Knowledge item not found: {knowledge_item_id}")
        if item.visibility_scope not in {"shared_region", "shared_global"}:
            raise ValueError("Only shared_region/shared_global knowledge can be published.")

        rendered = self.renderer.render(item)
        errors = self.validator.validate(rendered)
        if errors:
            item.review_status = "publish_failed"
            self.db.commit()
            raise ValueError("; ".join(errors))

        result = self._commit_or_mock(rendered.path, rendered.content)
        item.github_path = result.github_path
        item.github_commit_sha = result.commit_sha
        if item.review_status == "pending_republish":
            item.review_status = (
                "approved_global_shared"
                if item.visibility_scope == "shared_global"
                else "approved_region_shared"
            )
        self.audit.create(
            action="knowledge_published_github",
            target_type="knowledge_item",
            target_id=str(item.id),
            after_snapshot={"github_path": result.github_path, "commit_sha": result.commit_sha},
        )
        self.db.commit()
        return result

    def _commit_or_mock(self, path: str, content: str) -> PublishResult:
        settings = get_settings()
        if not settings.github_repo or not settings.github_token:
            digest = hashlib.sha1((path + content).encode("utf-8")).hexdigest()
            return PublishResult(github_path=path, commit_sha=f"mock-{digest[:12]}")

        url = f"https://api.github.com/repos/{settings.github_repo}/contents/{path}"
        import base64

        payload = {
            "message": f"publish knowledge: {path}",
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
            "branch": settings.github_branch,
        }
        headers = {
            "Authorization": f"Bearer {settings.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        with httpx.Client(timeout=20) as client:
            existing = client.get(
                url,
                headers=headers,
                params={"ref": settings.github_branch},
            )
            if existing.status_code == 200:
                payload["sha"] = existing.json()["sha"]
            elif existing.status_code != 404:
                existing.raise_for_status()
            response = client.put(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return PublishResult(github_path=path, commit_sha=data["commit"]["sha"])
