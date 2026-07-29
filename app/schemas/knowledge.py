from pydantic import BaseModel, Field


class KnowledgeSeedItem(BaseModel):
    owner_school_id: str | None = None
    knowledge_type: str
    title: str
    region_code: str | None = None
    visibility_scope: str = "shared_region"
    subject: str
    topic: str
    target_grade: int | None = None
    grade_min: int
    grade_max: int
    grade_mode: str = "range"
    content_th: str | None = None
    content_ms: str | None = None
    content_en: str | None = None
    local_context: str | None = None
    classroom_use: str | None = None
    safety_notes: str | None = None
    quality_score: int = Field(default=3, ge=1, le=5)
    source_type: str = "project_manual"
    source_confidence: str = "medium"
    source_note: str | None = None
    verified: bool = False
