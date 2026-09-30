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
    """
    if not DATABASE_URL.startswith("sqlite"):
        return

    inspector = inspect(engine)

    if "equipment" not in inspector.get_table_names():
        return

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

    legacy_table = "equipment_legacy_name_nullable"

    with engine.begin() as connection:
        connection.execute(
            text(f"DROP TABLE IF EXISTS {legacy_table}")
        )
        connection.execute(
            text(
                f"ALTER TABLE equipment RENAME TO {legacy_table}"
            )
        )

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
