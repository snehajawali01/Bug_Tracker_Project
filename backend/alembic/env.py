from logging.config import fileConfig

from alembic import context

from app.db.base import Base
from app.db.session import engine, DATABASE_URL

# Import models so SQLAlchemy registers their tables.
from app.models import User, Bug

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Make all model tables available to Alembic.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = DATABASE_URL.render_as_string(hide_password=False)

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
