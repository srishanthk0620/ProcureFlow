from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.db.session import get_db

from app.core.errors import Forbidden, Unauthorized
from app.models.enums import RoleName
from app.services.auth_service import DatabaseSessionService, Principal


bearer = HTTPBearer(auto_error=False)


def get_bearer_token(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise Unauthorized()
    return credentials.credentials


def get_current_principal(token: str = Depends(get_bearer_token), db: Session = Depends(get_db)) -> Principal:
    try:
        return DatabaseSessionService(db).resolve(token)
    finally:
        # End the read before a service reserves SQLite's writer. Writes revalidate.
        db.rollback()


def require_roles(*allowed: RoleName):
    def authorize(principal: Principal = Depends(get_current_principal)) -> Principal:
        if not principal.roles.intersection(allowed):
            raise Forbidden()
        return principal
    return authorize
