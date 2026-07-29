from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_school_code
from app.db.models.org import Region, School, Teacher


class OrgRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create_region(self, *, code: str, name: str, country_code: str = "th") -> Region:
        region = self.db.scalar(select(Region).where(Region.code == code))
        if region:
            return region
        region = Region(code=code, name=name, country_code=country_code)
        self.db.add(region)
        self.db.flush()
        return region

    def create_school(
        self,
        *,
        region: Region,
        name: str,
        school_code: str,
        school_type: str | None = None,
        resource_level: str = "low",
    ) -> School:
        school = School(
            region_id=region.id,
            name=name,
            school_code_hash=hash_school_code(school_code),
            school_code_rotated_at=datetime.now(UTC),
            school_type=school_type,
            resource_level=resource_level,
            active=True,
        )
        self.db.add(school)
        self.db.flush()
        return school

    def find_school_by_code(self, code: str) -> School | None:
        return self.db.scalar(
            select(School).where(School.school_code_hash == hash_school_code(code), School.active)
        )

    def get_school_by_id(self, school_id) -> School | None:
        return self.db.get(School, school_id)

    def list_schools(self, limit: int = 100) -> list[School]:
        return list(self.db.scalars(select(School).order_by(School.created_at.desc()).limit(limit)))

    def list_teachers(self, limit: int = 100) -> list[Teacher]:
        return list(self.db.scalars(select(Teacher).order_by(Teacher.created_at.desc()).limit(limit)))

    def get_teacher_by_line_user_id(self, line_user_id: str) -> Teacher | None:
        return self.db.scalar(select(Teacher).where(Teacher.line_user_id == line_user_id))

    def get_teacher_by_id(self, teacher_id) -> Teacher | None:
        return self.db.get(Teacher, teacher_id)

    def update_teacher_language(self, teacher: Teacher, language: str) -> Teacher:
        teacher.language_preference = language
        teacher.last_active_at = datetime.now(UTC)
        self.db.flush()
        return teacher

    def create_teacher_for_school(
        self,
        *,
        line_user_id: str,
        school: School,
        display_name: str | None = None,
    ) -> Teacher:
        teacher = Teacher(
            line_user_id=line_user_id,
            display_name=display_name,
            school_id=school.id,
            region_id=school.region_id,
            status="active",
            last_active_at=datetime.now(UTC),
        )
        self.db.add(teacher)
        self.db.flush()
        return teacher
