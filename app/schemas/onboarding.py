from uuid import UUID

from pydantic import BaseModel


class SchoolCreate(BaseModel):
    name: str
    region_code: str
    district_code: str | None = None
    school_type: str | None = None
    resource_level: str = "low"


class SchoolCreateResult(BaseModel):
    school_id: UUID
    school_code: str


class TeacherBindingResult(BaseModel):
    teacher_id: UUID
    school_id: UUID
    region_id: UUID
    school_name: str
    requires_consent: bool = True

