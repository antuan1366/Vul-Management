from pathlib import Path

from sqlalchemy import create_engine
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