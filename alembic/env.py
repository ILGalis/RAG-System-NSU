import os
import sys
from logging.config import fileConfig
from pathlib import Path

# Сначала добавляем корень проекта в sys.path, потом импортируем локальные модули
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import engine_from_config, pool

from alembic import context

from backend.core.config import settings
from backend.db.base import Base
from backend.models import (
    EmailVerificationToken,
    RagSpace,
    SpaceMember,
    User,
    UserSession,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# В тестах conftest подменяет os.environ["DATABASE_URL"] на тестовую БД
# перед вызовом alembic upgrade. Уважаем это переопределение, иначе берём
# значение из settings (который читает .env).
_migration_url = os.environ.get("DATABASE_URL") or settings.database_url
config.set_main_option("sqlalchemy.url", _migration_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
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
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
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