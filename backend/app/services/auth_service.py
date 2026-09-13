from dataclasses import dataclass
from typing import Protocol

from app.models.enums import RoleName


@dataclass(frozen=True)
class Principal:
    user_id: str
    roles: frozenset[RoleName]
    centre_ids: frozenset[str] = frozenset()


class SessionService(Protocol):
    """Implement with server-verified identity, expiry and revocation in P6B.

    Client role/user headers must never construct a trusted Principal.
    No token format, secret, default credential or OTP is supplied here.
    """
    def issue(self, user_id: str) -> str: ...
    def resolve(self, token: str) -> Principal: ...
    def revoke(self, token: str) -> None: ...
