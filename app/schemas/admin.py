from pydantic import BaseModel


class CreateSchoolRequest(BaseModel):
    name: str
    region_code: str = "pattani"
    region_name: str = "Pattani"
    country_code: str = "th"
    school_type: str | None = None
    resource_level: str = "low"


class CreateSchoolResponse(BaseModel):
    school_id: str
    school_code: str


class CreateAdminUserRequest(BaseModel):
    email: str
    password: str
    role: str = "school_admin"
    school_ids: list[str] = []
    region_ids: list[str] = []
    active: bool = True


class UpdateAdminUserRequest(BaseModel):
    password: str | None = None
    role: str | None = None
    school_ids: list[str] | None = None
    region_ids: list[str] | None = None
    active: bool | None = None
