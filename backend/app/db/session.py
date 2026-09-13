from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def make_engine(url: str, **kwargs) -> Engine:
    sqlite = make_url(url).get_backend_name() == "sqlite"
    engine = create_engine(url, connect_args={"check_same_thread": False} if sqlite else {}, **kwargs)
    if sqlite:
        @event.listens_for(engine, "connect")
        def sqlite_foreign_keys(connection, _record):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    return engine


# Engine/session factory are shared, never a mutable Session instance.
# Engine construction does not open a connection or create the SQLite file.
engine = make_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        # Services explicitly commit their unit of work; never commit on response teardown.
