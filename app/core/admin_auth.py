from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.db.session import SessionLocal

ROLE_LEVELS = {
    "viewer": 10,
    "operator": 20,
    "school_admin": 30,
    "reviewer": 30,
    "super_admin": 40,
}

security = HTTPBasic(auto_error=False)


@dataclass(frozen=True)
class AdminPrincipal:
    username: str
    role: str
    admin_id: str | None = None
    school_ids: tuple[str, ...] = ()
    region_ids: tuple[str, ...] = ()

    @property
    def is_scoped(self) -> bool:
        return self.role == "school_admin" or bool(self.school_ids or self.region_ids)


def authenticate_admin(username: str, password: str) -> AdminPrincipal | None:
    import secrets

    settings = get_settings()
    principal = _authenticate_database_admin(username, password)
    if principal is not None:
        return principal
    if _database_admin_exists(username):
        return None
    expected_password = settings.admin_password
    if not settings.admin_auth_enabled:
        return _principal_from_settings()
    if not expected_password:
        return None
    username_ok = secrets.compare_digest(username, settings.admin_username)
    password_ok = secrets.compare_digest(password, expected_password)
    if not username_ok or not password_ok:
        return None
    return _principal_from_settings(username=username)


def has_role(role: str, minimum_role: str) -> bool:
    return ROLE_LEVELS.get(role, 0) >= ROLE_LEVELS.get(minimum_role, 0)


def require_admin_user(
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
) -> AdminPrincipal:
    if not get_settings().admin_auth_enabled:
        return _principal_from_settings()
    if credentials is None:
        raise _unauthorized()
    principal = authenticate_admin(credentials.username, credentials.password)
    if principal is None:
        raise _unauthorized()
    return principal


def require_admin_role(minimum_role: str):
    def dependency(
        principal: Annotated[AdminPrincipal, Depends(require_admin_user)],
    ) -> AdminPrincipal:
        if not has_role(principal.role, minimum_role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role.")
        return principal

    return dependency


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Admin authentication required.",
        headers={"WWW-Authenticate": "Basic"},
    )


def _principal_from_settings(username: str | None = None) -> AdminPrincipal:
    settings = get_settings()
    return AdminPrincipal(
        admin_id=None,
        username=username or settings.admin_username,
        role=settings.admin_role,
        school_ids=_csv(settings.admin_school_ids),
        region_ids=_csv(settings.admin_region_ids),
    )


def _csv(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _authenticate_database_admin(username: str, password: str) -> AdminPrincipal | None:
    from sqlalchemy import select

    from app.core.security import verify_password
    from app.db.models.admin import AdminUser

    try:
        with SessionLocal() as db:
            admin = db.scalar(select(AdminUser).where(AdminUser.email == username, AdminUser.active))
            if not admin or not verify_password(password, admin.password_hash):
                return None
            return AdminPrincipal(
                admin_id=str(admin.id),
                username=admin.email,
                role=admin.role,
                school_ids=tuple(admin.school_ids or []),
                region_ids=tuple(admin.region_ids or []),
            )
    except SQLAlchemyError:
        return None


def _database_admin_exists(username: str) -> bool:
    from sqlalchemy import select

    from app.db.models.admin import AdminUser

    try:
        with SessionLocal() as db:
            return db.scalar(select(AdminUser.id).where(AdminUser.email == username)) is not None
    except SQLAlchemyError:
        return False
