from alembic import context

from app.core.config import settings
from app.db.base import Base
from app.db.session import make_engine
import app.models  # noqa: F401 -- register every table

config = context.config
target_metadata = Base.metadata


def configure(connection):
    context.configure(connection=connection, target_metadata=target_metadata,
                      compare_type=True, render_as_batch=connection.dialect.name == "sqlite")
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(url=settings.DATABASE_URL, target_metadata=target_metadata,
                      literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()
elif config.attributes.get("connection") is not None:
    # Isolated tests/autogeneration supply an explicit engine connection.
    configure(config.attributes["connection"])
else:
    engine = make_engine(settings.DATABASE_URL)
    try:
        with engine.connect() as connection:
            configure(connection)
    finally:
        engine.dispose()
