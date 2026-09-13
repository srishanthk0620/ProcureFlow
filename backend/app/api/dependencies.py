from fastapi import Depends

from app.core.errors import Forbidden, Unauthorized
from app.models.enums import RoleName
from app.services.auth_service import Principal


def get_current_principal() -> Principal:
    # Fail closed until the server-backed authentication adapter is implemented.
    raise Unauthorized()


def require_roles(*allowed: RoleName):
    def authorize(principal: Principal = Depends(get_current_principal)) -> Principal:
        if not principal.roles.intersection(allowed):
            raise Forbidden()
        return principal
    return authorize
