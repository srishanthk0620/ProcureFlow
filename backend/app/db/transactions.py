from contextlib import contextmanager
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError
from app.core.errors import Conflict


@contextmanager
def serialized_write(db: Session):
    """Reserve SQLite's writer before any capacity/identity reads.

    Never promote an already-open read transaction or silently commit caller work.
    Non-SQLite write support is deliberately fail-closed until locking is designed.
    """
    if db.in_transaction():
        raise RuntimeError("Write service requires a fresh transaction")
    if db.get_bind().dialect.name != "sqlite":
        raise RuntimeError("Prototype writes currently require SQLite")
    try:
        db.execute(text("BEGIN IMMEDIATE"))
        yield
        db.commit()
    except (IntegrityError, StaleDataError) as exc:
        db.rollback()
        raise Conflict() from exc
    except OperationalError as exc:
        db.rollback()
        if "locked" in str(exc.orig).lower() or "busy" in str(exc.orig).lower():
            raise Conflict() from exc
        raise
    except Exception:
        db.rollback()
        raise
