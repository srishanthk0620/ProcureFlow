"""Versioned scrypt password hashes using Python's OpenSSL-backed implementation."""
import base64
import hashlib
import hmac
import secrets

_N, _R, _P = 2**17, 8, 1
_MAX_MEMORY = 256 * 1024 * 1024


def _derive(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_N, r=_R, p=_P,
                          maxmem=_MAX_MEMORY, dklen=64)


def hash_password(password: str) -> str:
    if not 12 <= len(password) <= 1024:
        raise ValueError("Password must contain 12 to 1024 characters")
    salt = secrets.token_bytes(16)
    digest = _derive(password, salt)
    return "scrypt$v1$" + base64.b64encode(salt).decode("ascii") + "$" + base64.b64encode(digest).decode("ascii")


def verify_password(password: str, encoded: str | None) -> bool:
    if not isinstance(password, str) or not 12 <= len(password) <= 1024 or not encoded:
        return False
    try:
        algorithm, version, salt_text, digest_text = encoded.split("$")
        if algorithm != "scrypt" or version != "v1":
            return False
        salt = base64.b64decode(salt_text, validate=True)
        digest = base64.b64decode(digest_text, validate=True)
        if len(salt) != 16 or len(digest) != 64:
            return False
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(_derive(password, salt), digest)
