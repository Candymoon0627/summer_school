from collections.abc import Callable
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func, or_, select

from app.core.admin_auth import ROLE_LEVELS, AdminPrincipal, require_admin_role, require_admin_user
from app.core.config import get_settings
from app.core.security import hash_password
from app.core.sentry import capture_sentry_test_event
from app.db.models.admin import AdminUser
from app.db.models.knowledge import KnowledgeItem
from app.db.models.lesson import LessonRequest
from app.db.models.org import School, Teacher
from app.db.models.submission import Submission
from app.db.session import SessionLocal
from app.repositories.audit import AuditRepository
from app.repositories.knowledge import KnowledgeRepository
from app.repositories.lesson import LessonRepository
from app.repositories.media import MediaRepository
from app.repositories.org import OrgRepository
from app.repositories.submission import SubmissionRepository
from app.schemas.admin import (
    CreateAdminUserRequest,
    CreateSchoolRequest,
    CreateSchoolResponse,
    UpdateAdminUserRequest,
)
from app.schemas.knowledge import KnowledgeSeedItem
from app.schemas.submission import SubmissionAction, SubmissionCreate, SubmissionUpdate
from app.services.content_review import ContentReviewService
from app.services.coverage import CoverageService
from app.services.duplicate import DuplicateDetectionService
from app.services.knowledge import KnowledgeService
from app.services.lesson_generation import LessonGenerationService
from app.services.lesson_requests import LessonRequestService
from app.services.onboarding import OnboardingService
from app.services.publishing import GitHubPublishingService
from app.services.publishing_batch import KnowledgeBatchPublishingService
from app.services.rag import RagService
from app.services.storage import StorageService
from app.services.submissions import SubmissionService

router = APIRouter(dependencies=[Depends(require_admin_user)])
ADMIN_USER_DEP = Depends(require_admin_user)
OPERATOR_DEP = Depends(require_admin_role("operator"))
REVIEWER_DEP = Depends(require_admin_role("reviewer"))
SUPER_ADMIN_DEP = Depends(require_admin_role("super_admin"))


def _school_scope(current_admin: AdminPrincipal) -> list[UUID]:
    return [UUID(item) for item in current_admin.school_ids]


def _region_scope(db, current_admin: AdminPrincipal) -> list[UUID]:
    region_ids = {UUID(item) for item in current_admin.region_ids}
    school_ids = _school_scope(current_admin)
    if school_ids:
        rows = db.scalars(select(School.region_id).where(School.id.in_(school_ids))).all()
        region_ids.update(rows)
    return list(region_ids)


def _ensure_school_access(current_admin: AdminPrincipal, school_id: UUID | None) -> None:
    if not current_admin.is_scoped:
        return
    if school_id is None or school_id not in _school_scope(current_admin):
        raise HTTPException(status_code=403, detail="School admin cannot access this school.")


def _ensure_unscoped(current_admin: AdminPrincipal, action: str) -> None:
    if current_admin.is_scoped:
        raise HTTPException(status_code=403, detail=f"School admin cannot {action}.")


def _filter_school_scope(statement, current_admin: AdminPrincipal, column):
    if not current_admin.is_scoped:
        return statement
    return statement.where(column.in_(_school_scope(current_admin)))


def _knowledge_scope_condition(db, current_admin: AdminPrincipal):
    if not current_admin.is_scoped:
        return KnowledgeItem.is_deleted.is_(False)
    school_ids = _school_scope(current_admin)
    region_ids = _region_scope(db, current_admin)
    return and_(
        KnowledgeItem.is_deleted.is_(False),
        or_(
            KnowledgeItem.owner_school_id.in_(school_ids),
            and_(
                KnowledgeItem.visibility_scope == "shared_region",
                KnowledgeItem.owner_region_id.in_(region_ids),
            ),
            KnowledgeItem.visibility_scope == "shared_global",
        ),
    )


def _ensure_knowledge_access(db, current_admin: AdminPrincipal, item_id: str) -> KnowledgeItem:
    item = KnowledgeRepository(db).get_item(UUID(item_id))
    if not item or item.is_deleted:
        raise HTTPException(status_code=404, detail="Knowledge item not found.")
    if current_admin.is_scoped:
        school_ids = _school_scope(current_admin)
        region_ids = _region_scope(db, current_admin)
        allowed = (
            item.owner_school_id in school_ids
            or (item.visibility_scope == "shared_region" and item.owner_region_id in region_ids)
            or item.visibility_scope == "shared_global"
        )
        if not allowed:
            raise HTTPException(status_code=403, detail="School admin cannot access this knowledge item.")
    return item


def _ensure_school_owned_knowledge(current_admin: AdminPrincipal, item: KnowledgeItem) -> None:
    if not current_admin.is_scoped:
        return
    if item.owner_school_id not in _school_scope(current_admin):
        raise HTTPException(
            status_code=403,
            detail="School admin can only mutate school-owned knowledge items.",
        )


def _get_submission_for_admin(db, current_admin: AdminPrincipal, submission_id: str) -> Submission:
    submission = SubmissionRepository(db).get(UUID(submission_id))
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found.")
    _ensure_school_access(current_admin, submission.school_id)
    return submission


def _get_lesson_for_admin(db, current_admin: AdminPrincipal, lesson_request_id: str) -> LessonRequest:
    lesson = LessonRepository(db).get_request(UUID(lesson_request_id))
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson request not found.")
    _ensure_school_access(current_admin, lesson.school_id)
    return lesson


def _admin_user_summary(admin_user: AdminUser) -> dict:
    return {
        "id": str(admin_user.id),
        "email": admin_user.email,
        "role": admin_user.role,
        "school_ids": admin_user.school_ids or [],
        "region_ids": admin_user.region_ids or [],
        "active": admin_user.active,
        "created_at": admin_user.created_at.isoformat() if admin_user.created_at else None,
    }


def _validate_admin_role(role: str) -> None:
    if role not in ROLE_LEVELS:
        raise HTTPException(status_code=422, detail=f"Unknown admin role: {role}")


def _validate_admin_scope(db, school_ids: list[str], region_ids: list[str]) -> None:
    for school_id in school_ids:
        if not db.get(School, UUID(school_id)):
            raise HTTPException(status_code=422, detail=f"School not found: {school_id}")
    for region_id in region_ids:
        UUID(region_id)


def _lesson_status_counts(db, current_admin: AdminPrincipal) -> dict[str, int]:
    statement = (
        select(LessonRequest.status, func.count())
        .where(LessonRequest.school_id.in_(_school_scope(current_admin)))
        .group_by(LessonRequest.status)
    )
    return {status: count for status, count in db.execute(statement).all()}


def _submission_status_counts(db, current_admin: AdminPrincipal) -> dict[str, int]:
    statement = (
        select(Submission.status, func.count())
        .where(
            Submission.school_id.in_(_school_scope(current_admin)),
            Submission.status != "deleted",
        )
        .group_by(Submission.status)
    )
    return {status: count for status, count in db.execute(statement).all()}


def _knowledge_status_counts(db, current_admin: AdminPrincipal, field_name: str) -> dict[str, int]:
    field = getattr(KnowledgeItem, field_name)
    statement = (
        select(field, func.count())
        .where(_knowledge_scope_condition(db, current_admin))
        .group_by(field)
    )
    return {status: count for status, count in db.execute(statement).all()}


def _coverage_for_items(items: list[KnowledgeItem]) -> list[dict]:
    buckets: dict[tuple, dict] = {}
    for item in items:
        key = (
            str(item.owner_region_id) if item.owner_region_id else "global",
            item.subject,
            item.target_grade or f"{item.grade_min}-{item.grade_max}",
            item.topic,
            item.knowledge_type,
            item.visibility_scope,
        )
        bucket = buckets.setdefault(
            key,
            {
                "region_id": key[0],
                "subject": key[1],
                "grade": key[2],
                "topic": key[3],
                "knowledge_type": key[4],
                "visibility_scope": key[5],
                "knowledge_count": 0,
                "high_quality_count": 0,
                "embedded_count": 0,
            },
        )
        bucket["knowledge_count"] += 1
        if item.quality_score >= 4:
            bucket["high_quality_count"] += 1
        if item.vector_status == "embedded":
            bucket["embedded_count"] += 1
    return sorted(
        buckets.values(),
        key=lambda row: (row["knowledge_count"], row["high_quality_count"]),
        reverse=True,
    )


def _submission_summary(submission: Submission) -> dict:
    return {
        "id": str(submission.id),
        "status": submission.status,
        "stage": submission.current_review_stage,
        "source_type": submission.source_type,
        "teacher_id": str(submission.teacher_id) if submission.teacher_id else None,
        "school_id": str(submission.school_id) if submission.school_id else None,
        "region_id": str(submission.region_id) if submission.region_id else None,
        "knowledge_item_id": str(submission.knowledge_item_id)
        if submission.knowledge_item_id
        else None,
        "title": submission.title,
        "knowledge_type": submission.knowledge_type,
        "subject": submission.subject,
        "topic": submission.topic,
        "grade": submission.target_grade or f"{submission.grade_min}-{submission.grade_max}",
        "visibility_scope": submission.visibility_scope,
        "created_at": submission.created_at.isoformat() if submission.created_at else None,
        "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
        "published_at": submission.published_at.isoformat() if submission.published_at else None,
    }


def _submission_detail(submission: Submission) -> dict:
    return _submission_summary(submission) | {
        "target_grade": submission.target_grade,
        "grade_min": submission.grade_min,
        "grade_max": submission.grade_max,
        "content_th": submission.content_th,
        "content_ms": submission.content_ms,
        "content_en": submission.content_en,
        "local_context": submission.local_context,
        "classroom_use": submission.classroom_use,
        "safety_notes": submission.safety_notes,
        "source_note": submission.source_note,
        "sensitive_status": submission.sensitive_status,
        "copyright_status": submission.copyright_status,
        "duplicate_status": submission.duplicate_status,
        "first_reviewed_at": submission.first_reviewed_at.isoformat()
        if submission.first_reviewed_at
        else None,
        "second_reviewed_at": submission.second_reviewed_at.isoformat()
        if submission.second_reviewed_at
        else None,
        "embedded_at": submission.embedded_at.isoformat() if submission.embedded_at else None,
    }


def _submission_action(
    submission_id: str,
    current_admin: AdminPrincipal,
    action: Callable[[SubmissionService], Submission],
    *,
    require_private_school: bool = False,
) -> dict:
    with SessionLocal() as db:
        submission = _get_submission_for_admin(db, current_admin, submission_id)
        if (
            require_private_school
            and current_admin.is_scoped
            and submission.visibility_scope != "private_school"
        ):
            submission.visibility_scope = "private_school"
        try:
            submission = action(SubmissionService(db))
        except ValueError as exc:
            detail = str(exc)
            status_code = 404 if "not found" in detail.lower() else 409
            raise HTTPException(status_code=status_code, detail=detail) from exc
        return _submission_detail(submission)


@router.get("/me")
def me(current_admin: AdminPrincipal = ADMIN_USER_DEP) -> dict:
    return {
        "admin_id": current_admin.admin_id,
        "username": current_admin.username,
        "role": current_admin.role,
        "school_ids": list(current_admin.school_ids),
        "region_ids": list(current_admin.region_ids),
        "is_scoped": current_admin.is_scoped,
    }


@router.get("/users")
def list_admin_users(
    limit: int = 100,
    current_admin: AdminPrincipal = SUPER_ADMIN_DEP,
) -> dict:
    del current_admin
    with SessionLocal() as db:
        users = list(db.scalars(select(AdminUser).order_by(AdminUser.created_at.desc()).limit(limit)))
        return {"items": [_admin_user_summary(user) for user in users]}


@router.post("/users")
def create_admin_user(
    request: CreateAdminUserRequest,
    current_admin: AdminPrincipal = SUPER_ADMIN_DEP,
) -> dict:
    del current_admin
    _validate_admin_role(request.role)
    with SessionLocal() as db:
        _validate_admin_scope(db, request.school_ids, request.region_ids)
        existing = db.scalar(select(AdminUser).where(AdminUser.email == request.email.strip().lower()))
        if existing:
            raise HTTPException(status_code=409, detail="Admin user already exists.")
        user = AdminUser(
            provider="password",
            email=request.email.strip().lower(),
            password_hash=hash_password(request.password),
            role=request.role,
            school_ids=request.school_ids,
            region_ids=request.region_ids,
            active=request.active,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return _admin_user_summary(user)


@router.patch("/users/{admin_user_id}")
def update_admin_user(
    admin_user_id: str,
    request: UpdateAdminUserRequest,
    current_admin: AdminPrincipal = SUPER_ADMIN_DEP,
) -> dict:
    del current_admin
    with SessionLocal() as db:
        user = db.get(AdminUser, UUID(admin_user_id))
        if not user:
            raise HTTPException(status_code=404, detail="Admin user not found.")
        if request.role is not None:
            _validate_admin_role(request.role)
            user.role = request.role
        if request.school_ids is not None or request.region_ids is not None:
            school_ids = request.school_ids if request.school_ids is not None else user.school_ids or []
            region_ids = request.region_ids if request.region_ids is not None else user.region_ids or []
            _validate_admin_scope(db, school_ids, region_ids)
            user.school_ids = school_ids
            user.region_ids = region_ids
        if request.password:
            user.password_hash = hash_password(request.password)
            user.provider = "password"
        if request.active is not None:
            user.active = request.active
        db.commit()
        db.refresh(user)
        return _admin_user_summary(user)


@router.get("/status")
def status() -> dict:
    return {
        "api": "ok",
        "worker": "configured",
        "sentry": "configured" if get_settings().sentry_dsn else "not_configured",
    }


@router.get("/overview")
def overview(current_admin: AdminPrincipal = ADMIN_USER_DEP) -> dict:
    with SessionLocal() as db:
        knowledge = KnowledgeRepository(db)
        lessons = LessonRepository(db)
        schools_count = select(func.count()).select_from(School)
        teachers_count = select(func.count()).select_from(Teacher)
        knowledge_count = (
            select(func.count())
            .select_from(KnowledgeItem)
            .where(_knowledge_scope_condition(db, current_admin))
        )
        lessons_count = select(func.count()).select_from(LessonRequest)
        submissions_count = (
            select(func.count()).select_from(Submission).where(Submission.status != "deleted")
        )
        if current_admin.is_scoped:
            schools_count = _filter_school_scope(schools_count, current_admin, School.id)
            teachers_count = _filter_school_scope(teachers_count, current_admin, Teacher.school_id)
            lessons_count = _filter_school_scope(lessons_count, current_admin, LessonRequest.school_id)
            submissions_count = _filter_school_scope(
                submissions_count,
                current_admin,
                Submission.school_id,
            )
        return {
            "counts": {
                "schools": db.scalar(schools_count) or 0,
                "teachers": db.scalar(teachers_count) or 0,
                "knowledge_items": db.scalar(knowledge_count) or 0,
                "lesson_requests": db.scalar(lessons_count) or 0,
                "submissions": db.scalar(submissions_count) or 0,
            },
            "lesson_status": _lesson_status_counts(db, current_admin)
            if current_admin.is_scoped
            else lessons.status_counts(),
            "knowledge_review_status": _knowledge_status_counts(db, current_admin, "review_status")
            if current_admin.is_scoped
            else knowledge.review_status_counts(),
            "knowledge_vector_status": _knowledge_status_counts(db, current_admin, "vector_status")
            if current_admin.is_scoped
            else knowledge.vector_status_counts(),
            "submission_status": _submission_status_counts(db, current_admin)
            if current_admin.is_scoped
            else SubmissionRepository(db).status_counts(),
        }


@router.post("/dev/sentry-test")
def sentry_test_event(
    current_admin: AdminPrincipal = SUPER_ADMIN_DEP,
) -> dict:
    del current_admin
    settings = get_settings()
    if settings.environment != "development":
        raise HTTPException(status_code=403, detail="Sentry test events are development-only.")

    event_id = capture_sentry_test_event(source="api")
    if not event_id:
        return {"status": "not_configured", "event_id": None}
    return {"status": "sent", "event_id": event_id}


@router.post("/schools", response_model=CreateSchoolResponse)
def create_school(
    request: CreateSchoolRequest,
    current_admin: AdminPrincipal = OPERATOR_DEP,
) -> CreateSchoolResponse:
    _ensure_unscoped(current_admin, "create schools")
    with SessionLocal() as db:
        return OnboardingService(db).create_school_with_code(request)


@router.get("/schools")
def list_schools(
    limit: int = 100,
    offset: int = 0,
    q: str | None = None,
    current_admin: AdminPrincipal = ADMIN_USER_DEP,
) -> dict:
    with SessionLocal() as db:
        query = select(School)
        count_query = select(func.count()).select_from(School)
        query = _filter_school_scope(query, current_admin, School.id)
        count_query = _filter_school_scope(count_query, current_admin, School.id)
        if q:
            search = f"%{q.strip()}%"
            query = query.where(
                or_(
                    School.name.ilike(search),
                    School.resource_level.ilike(search),
                )
            )
            count_query = count_query.where(
                or_(
                    School.name.ilike(search),
                    School.resource_level.ilike(search),
                )
            )
        schools = list(
            db.scalars(query.order_by(School.created_at.desc()).offset(offset).limit(limit))
        )
        return {
            "total": db.scalar(count_query) or 0,
            "limit": limit,
            "offset": offset,
            "items": [
                {
                    "id": str(school.id),
                    "name": school.name,
                    "region_id": str(school.region_id),
                    "active": school.active,
                    "resource_level": school.resource_level,
                    "created_at": school.created_at.isoformat() if school.created_at else None,
                }
                for school in schools
            ]
        }


@router.get("/teachers")
def list_teachers(
    limit: int = 100,
    offset: int = 0,
    school_id: str | None = None,
    current_admin: AdminPrincipal = ADMIN_USER_DEP,
) -> dict:
    with SessionLocal() as db:
        query = select(Teacher)
        count_query = select(func.count()).select_from(Teacher)
        if school_id:
            school_uuid = UUID(school_id)
            _ensure_school_access(current_admin, school_uuid)
            query = query.where(Teacher.school_id == school_uuid)
            count_query = count_query.where(Teacher.school_id == school_uuid)
        else:
            query = _filter_school_scope(query, current_admin, Teacher.school_id)
            count_query = _filter_school_scope(count_query, current_admin, Teacher.school_id)
        teachers = list(
            db.scalars(query.order_by(Teacher.created_at.desc()).offset(offset).limit(limit))
        )
        return {
            "total": db.scalar(count_query) or 0,
            "limit": limit,
            "offset": offset,
            "items": [
                {
                    "id": str(teacher.id),
                    "line_user_id": teacher.line_user_id,
                    "school_id": str(teacher.school_id),
                    "region_id": str(teacher.region_id),
                    "status": teacher.status,
                    "last_active_at": teacher.last_active_at.isoformat()
                    if teacher.last_active_at
                    else None,
                    "created_at": teacher.created_at.isoformat() if teacher.created_at else None,
                }
                for teacher in teachers
            ]
        }


@router.post("/dev/bind-teacher")
def bind_teacher(
    line_user_id: str,
    school_code: str,
    current_admin: AdminPrincipal = OPERATOR_DEP,
) -> dict:
    with SessionLocal() as db:
        if current_admin.is_scoped:
            school = OrgRepository(db).find_school_by_code(school_code)
            if not school:
                return {"status": "invalid_school_code"}
            _ensure_school_access(current_admin, school.id)
        result = OnboardingService(db).bind_teacher_by_school_code(
            line_user_id=line_user_id,
            school_code=school_code,
        )
        if not result:
            return {"status": "invalid_school_code"}
        return {"status": "bound", **result.model_dump(mode="json")}


@router.post("/dev/lesson-request")
def create_lesson_request(
    line_user_id: str,
    text: str,
    enqueue: bool = False,
    current_admin: AdminPrincipal = OPERATOR_DEP,
) -> dict:
    with SessionLocal() as db:
        teacher = OrgRepository(db).get_teacher_by_line_user_id(line_user_id)
        if teacher:
            _ensure_school_access(current_admin, teacher.school_id)
        return LessonRequestService(db).create_from_teacher_text(
            line_user_id=line_user_id,
            text=text,
            enqueue=enqueue,
        )


@router.post("/dev/lesson-requests/{lesson_request_id}/generate-now")
def generate_lesson_now(
    lesson_request_id: str,
    current_admin: AdminPrincipal = OPERATOR_DEP,
) -> dict:
    from uuid import UUID

    with SessionLocal() as db:
        _get_lesson_for_admin(db, current_admin, lesson_request_id)
        lesson = LessonGenerationService(db).generate(UUID(lesson_request_id))
        return {
            "id": str(lesson.id),
            "status": lesson.status,
            "title": (lesson.structured_content or {}).get("title"),
            "docx_media_asset_id": str(lesson.docx_media_asset_id)
            if lesson.docx_media_asset_id
            else None,
        }


@router.get("/dev/teachers/{line_user_id}/history")
def teacher_history(line_user_id: str, current_admin: AdminPrincipal = ADMIN_USER_DEP) -> dict:
    with SessionLocal() as db:
        teacher = OrgRepository(db).get_teacher_by_line_user_id(line_user_id)
        if not teacher:
            return {"items": []}
        _ensure_school_access(current_admin, teacher.school_id)
        items = LessonRepository(db).recent_for_teacher(teacher.id)
        return {
            "items": [
                {
                    "id": str(item.id),
                    "subject": item.subject,
                    "grade": item.grade,
                    "topic": item.topic,
                    "status": item.status,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                }
                for item in items
            ]
        }


@router.get("/lessons")
def list_lessons(
    limit: int = 100,
    status: str | None = None,
    current_admin: AdminPrincipal = ADMIN_USER_DEP,
) -> dict:
    with SessionLocal() as db:
        query = select(LessonRequest).order_by(LessonRequest.created_at.desc()).limit(limit)
        if status:
            query = query.where(LessonRequest.status == status)
        query = _filter_school_scope(query, current_admin, LessonRequest.school_id)
        lessons = list(db.scalars(query))
        return {
            "items": [
                {
                    "id": str(lesson.id),
                    "teacher_id": str(lesson.teacher_id),
                    "school_id": str(lesson.school_id),
                    "region_id": str(lesson.region_id),
                    "subject": lesson.subject,
                    "grade": lesson.grade,
                    "topic": lesson.topic,
                    "status": lesson.status,
                    "rag_confidence": lesson.rag_confidence,
                    "model": f"{lesson.model_provider}:{lesson.model_name}"
                    if lesson.model_provider or lesson.model_name
                    else None,
                    "token_input": lesson.token_input,
                    "token_output": lesson.token_output,
                    "error_message": lesson.error_message,
                    "created_at": lesson.created_at.isoformat() if lesson.created_at else None,
                    "completed_at": lesson.completed_at.isoformat() if lesson.completed_at else None,
                }
                for lesson in lessons
            ]
        }


@router.get("/submissions")
def list_submissions(
    limit: int = 100,
    status: str | None = None,
    current_admin: AdminPrincipal = ADMIN_USER_DEP,
) -> dict:
    with SessionLocal() as db:
        query = select(Submission).order_by(Submission.created_at.desc()).limit(limit)
        if status:
            query = query.where(Submission.status == status)
        else:
            query = query.where(Submission.status != "deleted")
        query = _filter_school_scope(query, current_admin, Submission.school_id)
        submissions = list(db.scalars(query))
        return {"items": [_submission_summary(item) for item in submissions]}


@router.post("/submissions")
def create_submission(
    request: SubmissionCreate,
    current_admin: AdminPrincipal = REVIEWER_DEP,
) -> dict:
    if current_admin.is_scoped:
        school_ids = _school_scope(current_admin)
        if not school_ids:
            raise HTTPException(status_code=403, detail="School admin has no school scope.")
        requested_school_id = UUID(request.school_id) if request.school_id else school_ids[0]
        _ensure_school_access(current_admin, requested_school_id)
        request = request.model_copy(
            update={
                "school_id": str(requested_school_id),
                "visibility_scope": "private_school",
            }
        )
    with SessionLocal() as db:
        try:
            submission = SubmissionService(db).create_admin_submission(
                request,
                current_admin=current_admin,
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return _submission_summary(submission)


@router.get("/submissions/{submission_id}")
def submission_detail(submission_id: str, current_admin: AdminPrincipal = ADMIN_USER_DEP) -> dict:
    with SessionLocal() as db:
        submission = _get_submission_for_admin(db, current_admin, submission_id)
        reviews = SubmissionRepository(db).reviews_for_submission(submission.id)
        return _submission_detail(submission) | {
            "reviews": [
                {
                    "id": str(review.id),
                    "stage": review.stage,
                    "action": review.action,
                    "reviewer_username": review.reviewer_username,
                    "reviewer_role": review.reviewer_role,
                    "note": review.note,
                    "before_status": review.before_status,
                    "after_status": review.after_status,
                    "created_at": review.created_at.isoformat() if review.created_at else None,
                }
                for review in reviews
            ]
        }


@router.patch("/submissions/{submission_id}")
def update_submission(
    submission_id: str,
    request: SubmissionUpdate,
    current_admin: AdminPrincipal = REVIEWER_DEP,
) -> dict:
    with SessionLocal() as db:
        _get_submission_for_admin(db, current_admin, submission_id)
        if current_admin.is_scoped:
            request = request.model_copy(update={"visibility_scope": "private_school"})
        try:
            submission = SubmissionService(db).update_submission(
                UUID(submission_id),
                request,
                current_admin=current_admin,
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return _submission_detail(submission)


@router.post("/submissions/{submission_id}/submit")
def submit_submission(
    submission_id: str,
    action: SubmissionAction | None = None,
    current_admin: AdminPrincipal = REVIEWER_DEP,
) -> dict:
    return _submission_action(
        submission_id,
        current_admin,
        lambda service: service.submit_for_review(
            UUID(submission_id),
            current_admin=current_admin,
            note=action.note if action else None,
        ),
    )


@router.post("/submissions/{submission_id}/first-approve")
def first_approve_submission(
    submission_id: str,
    action: SubmissionAction | None = None,
    current_admin: AdminPrincipal = REVIEWER_DEP,
) -> dict:
    return _submission_action(
        submission_id,
        current_admin,
        lambda service: service.first_approve(
            UUID(submission_id),
            current_admin=current_admin,
            note=action.note if action else None,
        ),
    )


@router.post("/submissions/{submission_id}/second-approve")
def second_approve_submission(
    submission_id: str,
    action: SubmissionAction | None = None,
    current_admin: AdminPrincipal = REVIEWER_DEP,
) -> dict:
    return _submission_action(
        submission_id,
        current_admin,
        lambda service: service.second_approve(
            UUID(submission_id),
            current_admin=current_admin,
            note=action.note if action else None,
        ),
    )


@router.post("/submissions/{submission_id}/request-revision")
def request_submission_revision(
    submission_id: str,
    action: SubmissionAction | None = None,
    current_admin: AdminPrincipal = REVIEWER_DEP,
) -> dict:
    return _submission_action(
        submission_id,
        current_admin,
        lambda service: service.request_revision(
            UUID(submission_id),
            current_admin=current_admin,
            note=action.note if action else None,
        ),
    )


@router.post("/submissions/{submission_id}/reject")
def reject_submission(
    submission_id: str,
    action: SubmissionAction | None = None,
    current_admin: AdminPrincipal = REVIEWER_DEP,
) -> dict:
    return _submission_action(
        submission_id,
        current_admin,
        lambda service: service.reject(
            UUID(submission_id),
            current_admin=current_admin,
            note=action.note if action else None,
        ),
    )


@router.post("/submissions/{submission_id}/delete")
def delete_submission(
    submission_id: str,
    action: SubmissionAction | None = None,
    current_admin: AdminPrincipal = REVIEWER_DEP,
) -> dict:
    return _submission_action(
        submission_id,
        current_admin,
        lambda service: service.delete(
            UUID(submission_id),
            current_admin=current_admin,
            note=action.note if action else None,
        ),
    )


@router.post("/submissions/{submission_id}/publish-to-knowledge")
def publish_submission_to_knowledge(
    submission_id: str,
    current_admin: AdminPrincipal = REVIEWER_DEP,
) -> dict:
    return _submission_action(
        submission_id,
        current_admin,
        lambda service: service.publish_to_knowledge(
            UUID(submission_id),
            current_admin=current_admin,
        ),
        require_private_school=True,
    )


@router.get("/lessons/{lesson_request_id}")
def lesson_detail(
    lesson_request_id: str,
    include_signed_urls: bool = False,
    current_admin: AdminPrincipal = ADMIN_USER_DEP,
) -> dict:
    with SessionLocal() as db:
        lesson = _get_lesson_for_admin(db, current_admin, lesson_request_id)
        media = MediaRepository(db).lesson_docx_assets(lesson.id)
        assets = []
        for asset in media:
            row = {
                "id": str(asset.id),
                "purpose": asset.purpose,
                "object_key": asset.object_key,
                "file_size": asset.file_size,
                "storage_provider": asset.storage_provider,
            }
            if include_signed_urls:
                row["signed_url"] = StorageService().signed_url(asset.object_key)
            assets.append(row)
        refs = LessonRepository(db).knowledge_refs_for_request(lesson.id)
        return {
            "id": str(lesson.id),
            "raw_user_input": lesson.raw_user_input,
            "subject": lesson.subject,
            "grade": lesson.grade,
            "topic": lesson.topic,
            "status": lesson.status,
            "rag_confidence": lesson.rag_confidence,
            "error_message": lesson.error_message,
            "structured_content": lesson.structured_content,
            "docx_assets": assets,
            "knowledge_refs": [
                {
                    "knowledge_item_id": str(ref.knowledge_item_id),
                    "knowledge_item_version_id": str(ref.knowledge_item_version_id)
                    if ref.knowledge_item_version_id
                    else None,
                    "chunk_id": str(ref.chunk_id) if ref.chunk_id else None,
                    "rank": ref.rank,
                    "relevance_score": ref.relevance_score,
                }
                for ref in refs
            ],
        }


@router.post("/knowledge/seed")
def import_seed_knowledge(
    item: KnowledgeSeedItem,
    current_admin: AdminPrincipal = REVIEWER_DEP,
) -> dict:
    if current_admin.is_scoped:
        school_ids = _school_scope(current_admin)
        if not school_ids:
            raise HTTPException(status_code=403, detail="School admin has no school scope.")
        owner_school_id = UUID(item.owner_school_id) if item.owner_school_id else school_ids[0]
        _ensure_school_access(current_admin, owner_school_id)
        item = item.model_copy(
            update={
                "owner_school_id": str(owner_school_id),
                "visibility_scope": "private_school",
                "verified": False,
            }
        )
    with SessionLocal() as db:
        knowledge = KnowledgeService(db).import_seed_item(item)
        return {
            "id": str(knowledge.id),
            "status": knowledge.review_status,
            "vector_status": knowledge.vector_status,
        }


@router.get("/knowledge")
def list_knowledge(limit: int = 100, current_admin: AdminPrincipal = ADMIN_USER_DEP) -> dict:
    with SessionLocal() as db:
        if current_admin.is_scoped:
            items = list(
                db.scalars(
                    select(KnowledgeItem)
                    .where(_knowledge_scope_condition(db, current_admin))
                    .order_by(KnowledgeItem.created_at.desc())
                    .limit(limit)
                )
            )
        else:
            items = KnowledgeRepository(db).list_items(limit=limit)
        return {
            "items": [
                {
                    "id": str(item.id),
                    "owner_school_id": str(item.owner_school_id) if item.owner_school_id else None,
                    "owner_region_id": str(item.owner_region_id) if item.owner_region_id else None,
                    "title": item.title,
                    "knowledge_type": item.knowledge_type,
                    "subject": item.subject,
                    "topic": item.topic,
                    "target_grade": item.target_grade,
                    "grade_min": item.grade_min,
                    "grade_max": item.grade_max,
                    "visibility_scope": item.visibility_scope,
                    "review_status": item.review_status,
                    "vector_status": item.vector_status,
                    "github_path": item.github_path,
                    "github_commit_sha": item.github_commit_sha,
                }
                for item in items
            ]
        }


@router.get("/knowledge/{knowledge_item_id}/versions")
def knowledge_versions(
    knowledge_item_id: str,
    current_admin: AdminPrincipal = ADMIN_USER_DEP,
) -> dict:
    with SessionLocal() as db:
        _ensure_knowledge_access(db, current_admin, knowledge_item_id)
        versions = KnowledgeRepository(db).list_versions(UUID(knowledge_item_id))
        return {
            "items": [
                {
                    "id": str(version.id),
                    "version_number": version.version_number,
                    "change_type": version.change_type,
                    "change_summary": version.change_summary,
                    "created_at": version.created_at.isoformat() if version.created_at else None,
                }
                for version in versions
            ]
        }


@router.get("/coverage")
def coverage(limit: int = 1000, current_admin: AdminPrincipal = ADMIN_USER_DEP) -> dict:
    with SessionLocal() as db:
        if current_admin.is_scoped:
            items = list(
                db.scalars(
                    select(KnowledgeItem)
                    .where(_knowledge_scope_condition(db, current_admin))
                    .order_by(KnowledgeItem.created_at.desc())
                    .limit(limit)
                )
            )
            return {"items": _coverage_for_items(items)}
        return {"items": CoverageService(db).knowledge_coverage(limit=limit)}


@router.get("/audit-logs")
def audit_logs(limit: int = 100, current_admin: AdminPrincipal = ADMIN_USER_DEP) -> dict:
    if current_admin.is_scoped:
        return {"items": []}
    with SessionLocal() as db:
        logs = AuditRepository(db).list_recent(limit=limit)
        return {
            "items": [
                {
                    "id": str(log.id),
                    "action": log.action,
                    "target_type": log.target_type,
                    "target_id": log.target_id,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in logs
            ]
        }


@router.post("/knowledge/{knowledge_item_id}/reembed")
def reembed_knowledge(
    knowledge_item_id: str,
    current_admin: AdminPrincipal = REVIEWER_DEP,
) -> dict:
    with SessionLocal() as db:
        item = _ensure_knowledge_access(db, current_admin, knowledge_item_id)
        _ensure_school_owned_knowledge(current_admin, item)
        chunks = KnowledgeService(db).rebuild_chunks_and_embedding(knowledge_item_id)
        return {"status": "embedded", "chunks": len(chunks)}


@router.post("/knowledge/{knowledge_item_id}/approve-school-private")
def approve_school_private(
    knowledge_item_id: str,
    current_admin: AdminPrincipal = REVIEWER_DEP,
) -> dict:
    with SessionLocal() as db:
        item = _ensure_knowledge_access(db, current_admin, knowledge_item_id)
        _ensure_school_owned_knowledge(current_admin, item)
        item = KnowledgeService(db).approve_school_private(knowledge_item_id)
        return {"id": str(item.id), "review_status": item.review_status}


@router.post("/knowledge/{knowledge_item_id}/approve-region-shared")
def approve_region_shared(
    knowledge_item_id: str,
    current_admin: AdminPrincipal = REVIEWER_DEP,
) -> dict:
    _ensure_unscoped(current_admin, "approve region-shared knowledge")
    with SessionLocal() as db:
        _ensure_knowledge_access(db, current_admin, knowledge_item_id)
        item = KnowledgeService(db).approve_region_shared(knowledge_item_id)
        return {"id": str(item.id), "review_status": item.review_status}


@router.post("/knowledge/{knowledge_item_id}/soft-delete")
def soft_delete_knowledge(
    knowledge_item_id: str,
    reason: str | None = None,
    current_admin: AdminPrincipal = REVIEWER_DEP,
) -> dict:
    with SessionLocal() as db:
        item = _ensure_knowledge_access(db, current_admin, knowledge_item_id)
        _ensure_school_owned_knowledge(current_admin, item)
        item = KnowledgeService(db).soft_delete(knowledge_item_id, reason)
        return {"id": str(item.id), "review_status": item.review_status, "is_deleted": item.is_deleted}


@router.post("/knowledge/{knowledge_item_id}/restore/{version_number}")
def restore_knowledge_version(
    knowledge_item_id: str,
    version_number: int,
    current_admin: AdminPrincipal = REVIEWER_DEP,
) -> dict:
    with SessionLocal() as db:
        item = _ensure_knowledge_access(db, current_admin, knowledge_item_id)
        _ensure_school_owned_knowledge(current_admin, item)
        item = KnowledgeService(db).restore_version(knowledge_item_id, version_number)
        return {"id": str(item.id), "review_status": item.review_status, "vector_status": item.vector_status}


@router.post("/knowledge/{knowledge_item_id}/reject")
def reject_knowledge(
    knowledge_item_id: str,
    reason: str | None = None,
    current_admin: AdminPrincipal = REVIEWER_DEP,
) -> dict:
    with SessionLocal() as db:
        item = _ensure_knowledge_access(db, current_admin, knowledge_item_id)
        _ensure_school_owned_knowledge(current_admin, item)
        item = KnowledgeService(db).reject(knowledge_item_id, reason)
        return {"id": str(item.id), "review_status": item.review_status}


@router.post("/knowledge/{knowledge_item_id}/sensitive-check")
def sensitive_check(
    knowledge_item_id: str,
    current_admin: AdminPrincipal = REVIEWER_DEP,
) -> dict:
    with SessionLocal() as db:
        item = _ensure_knowledge_access(db, current_admin, knowledge_item_id)
        _ensure_school_owned_knowledge(current_admin, item)
        return ContentReviewService(db).run_sensitive_check(knowledge_item_id)


@router.post("/knowledge/{knowledge_item_id}/copyright-check")
def copyright_check(
    knowledge_item_id: str,
    current_admin: AdminPrincipal = REVIEWER_DEP,
) -> dict:
    with SessionLocal() as db:
        item = _ensure_knowledge_access(db, current_admin, knowledge_item_id)
        _ensure_school_owned_knowledge(current_admin, item)
        return ContentReviewService(db).run_copyright_check(knowledge_item_id)


@router.post("/knowledge/{knowledge_item_id}/duplicate-check")
def duplicate_check(
    knowledge_item_id: str,
    threshold: float = 0.82,
    current_admin: AdminPrincipal = REVIEWER_DEP,
) -> dict:
    with SessionLocal() as db:
        item = _ensure_knowledge_access(db, current_admin, knowledge_item_id)
        _ensure_school_owned_knowledge(current_admin, item)
        candidates = DuplicateDetectionService(db).detect_for_item(knowledge_item_id, threshold)
        return {"candidates": candidates}


@router.post("/knowledge/{duplicate_item_id}/merge-into/{main_item_id}")
def merge_duplicate(
    duplicate_item_id: str,
    main_item_id: str,
    current_admin: AdminPrincipal = REVIEWER_DEP,
) -> dict:
    _ensure_unscoped(current_admin, "merge duplicate knowledge")
    with SessionLocal() as db:
        return DuplicateDetectionService(db).merge_duplicate(
            duplicate_item_id=duplicate_item_id,
            main_item_id=main_item_id,
        )


@router.post("/knowledge/{knowledge_item_id}/publish")
def publish_knowledge(
    knowledge_item_id: str,
    current_admin: AdminPrincipal = SUPER_ADMIN_DEP,
) -> dict:
    del current_admin
    with SessionLocal() as db:
        result = GitHubPublishingService(db).publish_knowledge_item(knowledge_item_id)
        return {"github_path": result.github_path, "commit_sha": result.commit_sha}


@router.get("/publishing/candidates")
def publishing_candidates(
    region: str | None = None,
    subject: str | None = None,
    limit: int = 100,
    allow_test_data: bool = False,
    current_admin: AdminPrincipal = ADMIN_USER_DEP,
) -> dict:
    _ensure_unscoped(current_admin, "list GitHub publishing candidates")
    with SessionLocal() as db:
        candidates = KnowledgeBatchPublishingService(db).candidates(
            region_code=region,
            subject=subject,
            allow_test_data=allow_test_data,
            limit=limit,
        )
        return {"items": [candidate.__dict__ for candidate in candidates]}


@router.post("/publishing/batch")
def publish_batch(
    region: str | None = None,
    subject: str | None = None,
    limit: int = 100,
    allow_test_data: bool = False,
    allow_warnings: bool = False,
    execute: bool = False,
    current_admin: AdminPrincipal = SUPER_ADMIN_DEP,
) -> dict:
    del current_admin
    with SessionLocal() as db:
        try:
            result = KnowledgeBatchPublishingService(db).publish(
                region_code=region,
                subject=subject,
                allow_test_data=allow_test_data,
                allow_warnings=allow_warnings,
                limit=limit,
                dry_run=not execute,
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {
            "dry_run": not execute,
            "candidates": [candidate.__dict__ for candidate in result.candidates],
            "published": [
                {"github_path": item.github_path, "commit_sha": item.commit_sha}
                for item in result.published
            ],
        }


@router.get("/dev/rag-search")
def rag_search(
    line_user_id: str,
    subject: str,
    grade: int,
    topic: str,
    current_admin: AdminPrincipal = ADMIN_USER_DEP,
) -> dict:
    with SessionLocal() as db:
        teacher = OrgRepository(db).get_teacher_by_line_user_id(line_user_id)
        if not teacher:
            return {"status": "teacher_not_found", "items": []}
        _ensure_school_access(current_admin, teacher.school_id)
        items, confidence = RagService(db).retrieve_for_lesson(
            teacher_id=str(teacher.id),
            school_id=str(teacher.school_id),
            region_id=str(teacher.region_id),
            subject=subject,
            grade=grade,
            topic=topic,
        )
        return {
            "confidence": confidence,
            "items": [
                {
                    "knowledge_item_id": item.knowledge_item_id,
                    "title": item.title,
                    "score": item.score,
                }
                for item in items
            ],
        }
