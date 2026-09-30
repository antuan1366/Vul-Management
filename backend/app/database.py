from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


DATABASE_URL = settings.database_url


if DATABASE_URL.startswith("sqlite:///"):
    database_path = DATABASE_URL.replace(
        "sqlite:///",
        "",
        1,
    )

    Path(database_path).parent.mkdir(
        parents=True,
        exist_ok=True,
    )


connect_args = {}


if DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False,
    }


engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def migrate_equipment_name_nullable():
    """
    Rebuild the SQLite equipment table when an older database still has
    equipment.name as NOT NULL.

    The migration also handles an interrupted previous migration where the
    old table was already renamed to the legacy table.
    """
    if not DATABASE_URL.startswith("sqlite"):
        return

    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    legacy_table = "equipment_legacy_name_nullable"
    equipment_exists = "equipment" in table_names
    legacy_exists = legacy_table in table_names

    if not equipment_exists and not legacy_exists:
        return

    if equipment_exists:
        name_column = next(
            (
                column
                for column in inspector.get_columns("equipment")
                if column["name"] == "name"
            ),
            None,
        )

        if not name_column or name_column.get("nullable", True):
            return

        # SQLite cannot directly change a NOT NULL column to nullable.
        # Save the existing index names before renaming the table because
        # SQLite keeps those index names after the table is renamed.
        equipment_indexes = [
            index["name"]
            for index in inspector.get_indexes("equipment")
            if index.get("name")
        ]

        with engine.begin() as connection:
            connection.execute(
                text(f"DROP TABLE IF EXISTS {legacy_table}")
            )

            connection.execute(
                text(
                    f"ALTER TABLE equipment RENAME TO {legacy_table}"
                )
            )

            for index_name in equipment_indexes:
                connection.execute(
                    text(
                        f'DROP INDEX IF EXISTS "{index_name}"'
                    )
                )

    # Refresh SQLAlchemy's view of the database after the rename.
    Base.metadata.create_all(bind=engine)

    column_names = [
        "id",
        "name",
        "device_type",
        "vendor",
        "model",
        "version",
        "ip_address",
        "serial_number",
        "cpe",
        "criticality",
        "environment",
        "description",
        "created_at",
        "updated_at",
    ]

    columns_sql = ", ".join(column_names)

    with engine.begin() as connection:
        connection.execute(
            text(
                f"""
                INSERT INTO equipment ({columns_sql})
                SELECT {columns_sql}
                FROM {legacy_table}
                """
            )
        )

        connection.execute(
            text(f"DROP TABLE {legacy_table}")
        )
