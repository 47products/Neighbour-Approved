"""Alembic environment configuration."""

from logging.config import fileConfig
import os
from pathlib import Path
import re

from sqlalchemy import engine_from_config
from sqlalchemy import pool, text
from dotenv import load_dotenv
from alembic import context

# Load environment variables from .env file
env_path = Path(__file__).parents[2] / ".env"
load_dotenv(env_path)

from app.db.database_engine import Base
from app.db.database_settings import Settings
from app.db import models

# Load the Alembic configuration
config = context.config

# Configure logging from the alembic.ini file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the target metadata for migrations
target_metadata = Base.metadata


def get_url():
    """Retrieve database URL from settings."""
    try:
        settings = Settings()
        return str(settings.database_url)
    except Exception as e:
        print("\nError loading database configuration:")
        print("Current environment variables:")
        print(f"POSTGRES_USER: {os.getenv('POSTGRES_USER', 'Not set')}")
        print(f"POSTGRES_HOST: {os.getenv('POSTGRES_HOST', 'Not set')}")
        print(f"POSTGRES_DB: {os.getenv('POSTGRES_DB', 'Not set')}")
        print("POSTGRES_PASSWORD: [Hidden]")
        raise RuntimeError(f"Database configuration error: {str(e)}") from e


def include_object(object, name, type_, reflected, compare_to):
    """Decide whether to include an object in the migration."""
    # Skip certain types of indices
    if type_ == "index":
        # Skip temporary indices
        if name.startswith("tmp_"):
            return False
        # Skip auto-generated indices
        if re.match(r"ix_.*_tmp_\d+", name):
            return False
    return True


def run_migrations_offline() -> None:
    """Execute migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Execute migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=include_object,
            include_schemas=True,
            transaction_per_migration=True,
            compare_server_default=True,
        )

        # Enable pg_trgm extension if not exists
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
