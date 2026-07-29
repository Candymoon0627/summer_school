from pydantic import BaseModel, Field


class SubmissionCreate(BaseModel):
    teacher_id: str | None = None
    school_id: str | None = None
    region_id: str | None = None
    visibility_scope: str = "shared_region"
    knowledge_type: str = "local_example"
    subject: str = "general"
    topic: str = "teacher contribution"
    title: str
    target_grade: int | None = Field(default=None, ge=1, le=12)
    grade_min: int = Field(default=1, ge=1, le=12)
    grade_max: int = Field(default=12, ge=1, le=12)
    content_th: str | None = None
    content_ms: str | None = None
    content_en: str | None = None
    local_context: str | None = None
    classroom_use: str | None = None
    safety_notes: str | None = None
    source_note: str | None = None
    submit: bool = False


class SubmissionUpdate(BaseModel):
    visibility_scope: str | None = None
    knowledge_type: str | None = None
    subject: str | None = None
    topic: str | None = None
    title: str | None = None
    target_grade: int | None = Field(default=None, ge=1, le=12)
    grade_min: int | None = Field(default=None, ge=1, le=12)
    grade_max: int | None = Field(default=None, ge=1, le=12)
    content_th: str | None = None
    content_ms: str | None = None
    content_en: str | None = None
    local_context: str | None = None
    classroom_use: str | None = None
    safety_notes: str | None = None
    source_note: str | None = None


class SubmissionAction(BaseModel):
    note: str | None = None
