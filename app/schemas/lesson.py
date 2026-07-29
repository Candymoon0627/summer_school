from pydantic import BaseModel, Field


class LessonTerm(BaseModel):
    term_th: str
    helper_ms: str
    helper_en: str
    teacher_note: str | None = None


class LessonFlowStep(BaseModel):
    phase: str
    minutes: int | None = None
    teacher_action: str
    student_action: str | None = None


class TrilingualText(BaseModel):
    th: str
    ms: str
    en: str


class TrilingualLessonFlowStep(BaseModel):
    phase: TrilingualText
    minutes: int | None = None
    teacher_action: TrilingualText
    student_action: TrilingualText | None = None


class StructuredLesson(BaseModel):
    title: str
    title_trilingual: TrilingualText | None = None
    summary: str
    summary_trilingual: TrilingualText | None = None
    teaching_objectives: list[str] = Field(default_factory=list)
    teaching_objectives_trilingual: list[TrilingualText] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    materials_trilingual: list[TrilingualText] = Field(default_factory=list)
    lesson_flow: list[LessonFlowStep] = Field(default_factory=list)
    lesson_flow_trilingual: list[TrilingualLessonFlowStep] = Field(default_factory=list)
    local_examples: list[str] = Field(default_factory=list)
    local_examples_trilingual: list[TrilingualText] = Field(default_factory=list)
    key_terms_trilingual: list[LessonTerm] = Field(default_factory=list)
    student_activity: str
    student_activity_trilingual: TrilingualText | None = None
    practice_questions: list[str] = Field(default_factory=list)
    practice_questions_trilingual: list[TrilingualText] = Field(default_factory=list)
    board_plan: str
    board_plan_trilingual: TrilingualText | None = None
    low_resource_plan: str
    low_resource_plan_trilingual: TrilingualText | None = None
    safety_notes: str | None = None
    safety_notes_trilingual: TrilingualText | None = None
    local_knowledge_used: list[str] = Field(default_factory=list)


class LessonRequestCreate(BaseModel):
    line_user_id: str
    text: str


class LessonGenerationResult(BaseModel):
    structured_content: StructuredLesson
    rendered_markdown: str
    token_input: int = 0
    token_output: int = 0
