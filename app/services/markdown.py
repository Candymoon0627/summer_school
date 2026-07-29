import re
from dataclasses import dataclass
from typing import ClassVar

from app.db.models.knowledge import KnowledgeItem


@dataclass(frozen=True)
class RenderedMarkdown:
    path: str
    content: str


class KnowledgeMarkdownRenderer:
    def render(self, item: KnowledgeItem) -> RenderedMarkdown:
        path = self.path_for(item)
        front_matter = {
            "id": str(item.id),
            "knowledge_type": item.knowledge_type,
            "country": "th",
            "region_id": str(item.owner_region_id) if item.owner_region_id else None,
            "visibility_scope": item.visibility_scope,
            "subject": item.subject,
            "topic": item.topic,
            "target_grade": item.target_grade,
            "grade_min": item.grade_min,
            "grade_max": item.grade_max,
            "quality_score": item.quality_score,
            "sensitive_tags": item.sensitive_tags or [],
            "copyright_status": item.copyright_status,
            "review_status": item.review_status,
            "source_type": item.source_type,
            "source_confidence": item.source_confidence,
            "source_note": item.source_note,
        }
        yaml_lines = ["---"]
        for key, value in front_matter.items():
            yaml_lines.append(f"{key}: {self._yaml_value(value)}")
        yaml_lines.append("---")
        body = f"""
# {item.title}

## Thai

{item.content_th or ""}

## Local Malay Helper

{item.content_ms or ""}

## English

{item.content_en or ""}

## Local Context

{item.local_context or ""}

## Classroom Use

{item.classroom_use or ""}

## Safety Notes

{item.safety_notes or ""}
"""
        return RenderedMarkdown(path=path, content="\n".join(yaml_lines) + "\n" + body)

    def path_for(self, item: KnowledgeItem) -> str:
        grade = (
            f"grade-{item.target_grade}"
            if item.target_grade and item.grade_min == item.grade_max
            else f"grade-{item.grade_min}-{item.grade_max}"
        )
        slug = self._slug(f"{item.topic}-{item.title}")[:80]
        filename = f"{slug}-{str(item.id)[:8]}.md"
        if item.visibility_scope == "shared_global":
            return f"knowledge/global/{item.subject}/{grade}/{filename}"
        region = str(item.owner_region_id or "unknown-region")
        return f"knowledge/countries/th/regions/{region}/{item.subject}/{grade}/{filename}"

    def _slug(self, text: str) -> str:
        lowered = text.lower()
        lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
        return lowered.strip("-") or "knowledge"

    def _yaml_value(self, value) -> str:
        if value is None:
            return "null"
        if isinstance(value, list):
            return "[" + ", ".join(str(item) for item in value) + "]"
        if isinstance(value, str):
            return '"' + value.replace('"', '\\"') + '"'
        return str(value)


class KnowledgeMarkdownValidator:
    required_markers: ClassVar[list[str]] = [
        "---",
        "id:",
        "knowledge_type:",
        "visibility_scope:",
        "review_status:",
        "# ",
        "## Local Context",
        "## Classroom Use",
        "## Safety Notes",
    ]

    def validate(self, rendered: RenderedMarkdown) -> list[str]:
        errors = []
        for marker in self.required_markers:
            if marker not in rendered.content:
                errors.append(f"Missing marker: {marker}")
        if "private_school" in rendered.content:
            errors.append("Private school knowledge must not be published to GitHub.")
        return errors
