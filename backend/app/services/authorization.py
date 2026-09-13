from sqlalchemy.orm import Session
from app.core.errors import Forbidden
from app.models.enums import RoleName
from app.services.auth_service import Principal, principal_for, validate_actor
from app.models import AuthSession

OPERATORS = frozenset({RoleName.STAFF, RoleName.CENTRE_MANAGER})


def centre_access(db: Session, actor: Principal, centre_id: str | None = None) -> str:
    """Revalidate persisted roles and assignment, including inside write transactions.

    District/state/super-admin roles remain modeled but receive no implicit scope.
    """
    user = validate_actor(db, actor)
    current = principal_for(db, db.get(AuthSession, actor.session_id))
    if not current.roles.intersection(OPERATORS) or user.staff_profile is None:
        raise Forbidden()
    assigned = user.staff_profile.centre_id
    if centre_id is not None and centre_id != assigned:
        raise Forbidden()
    return assigned
