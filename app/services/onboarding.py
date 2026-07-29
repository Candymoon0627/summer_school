from sqlalchemy.orm import Session

from app.core.security import generate_school_code
from app.repositories.org import OrgRepository
from app.schemas.admin import CreateSchoolRequest, CreateSchoolResponse
from app.schemas.onboarding import TeacherBindingResult


class OnboardingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.orgs = OrgRepository(db)

    def create_school_with_code(self, request: CreateSchoolRequest) -> CreateSchoolResponse:
        region = self.orgs.get_or_create_region(
            code=request.region_code,
            name=request.region_name,
            country_code=request.country_code,
        )
        school_code = generate_school_code()
        school = self.orgs.create_school(
            region=region,
            name=request.name,
            school_code=school_code,
            school_type=request.school_type,
            resource_level=request.resource_level,
        )
        self.db.commit()
        return CreateSchoolResponse(school_id=str(school.id), school_code=school_code)

    def bind_teacher_by_school_code(
        self,
        *,
        line_user_id: str,
        school_code: str,
        display_name: str | None = None,
    ) -> TeacherBindingResult | None:
        existing = self.orgs.get_teacher_by_line_user_id(line_user_id)
        if existing:
            school = self.orgs.get_school_by_id(existing.school_id)
            return TeacherBindingResult(
                teacher_id=existing.id,
                school_id=existing.school_id,
                region_id=existing.region_id,
                school_name=school.name if school else "already_bound",
                requires_consent=existing.consent_version_id is None,
            )

        school = self.orgs.find_school_by_code(school_code)
        if not school:
            return None

        teacher = self.orgs.create_teacher_for_school(
            line_user_id=line_user_id,
            school=school,
            display_name=display_name,
        )
        self.db.commit()
        return TeacherBindingResult(
            teacher_id=teacher.id,
            school_id=school.id,
            region_id=school.region_id,
            school_name=school.name,
            requires_consent=True,
        )
