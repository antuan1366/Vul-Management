from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

from app.core.config import settings
from app.database import engine


def _alembic_config() -> Config:
    backend_dir = Path(__file__).resolve().parents[2]
    config = Config(str(backend_dir / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    return config


def get_current_database_revision() -> str | None:
    with engine.connect() as connection:
        migration_context = MigrationContext.configure(connection)
        return migration_context.get_current_revision()


def get_current_database_schema_version() -> int:
    revision = get_current_database_revision()

    if revision is None:
        raise RuntimeError(
            "Database has no Alembic revision. "
            "Run the database bootstrap/migration process first."
        )

    if not revision.isdigit():
        raise RuntimeError(
            f"Database revision '{revision}' is not a numeric schema revision."
        )

    return int(revision)


def ensure_database_version(fresh_database: bool = False) -> int:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    config = _alembic_config()
    script = ScriptDirectory.from_config(config)
    head = script.get_current_head()

    if head is None:
        raise RuntimeError("No Alembic migration head is configured.")

    if "alembic_version" not in table_names:
        if fresh_database:
            command.stamp(config, "head")
        else:
            command.stamp(config, "0001")

    current = get_current_database_revision()

    if current != head:
        command.upgrade(config, "head")

    return get_current_database_schema_version()


def validate_database_compatibility(database_schema_version: int) -> None:
    minimum = settings.db_schema_min
    maximum = settings.db_schema_max

    if minimum > maximum:
        raise RuntimeError(
            f"Invalid database compatibility window: "
            f"{minimum} > {maximum}."
        )

    if not minimum <= database_schema_version <= maximum:
        raise RuntimeError(
            "Database schema is incompatible with this application. "
            f"Application: {settings.app_version}; "
            f"supported DB schema: {minimum}-{maximum}; "
            f"current DB schema: {database_schema_version}."
        )
