from collections.abc import Generator

from sqlalchemy import MetaData, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


engine = create_engine(settings.database_url, future=True, pool_pre_ping=True)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def _ensure_runtime_schema() -> None:
    inspector = inspect(engine)

    if "admins" in inspector.get_table_names():
        existing_columns = {column["name"] for column in inspector.get_columns("admins")}
        statements = []
        if "full_name" not in existing_columns:
            statements.append("ALTER TABLE admins ADD COLUMN full_name VARCHAR(150)")
        if "position" not in existing_columns:
            statements.append("ALTER TABLE admins ADD COLUMN position VARCHAR(150)")
        if "about" not in existing_columns:
            statements.append("ALTER TABLE admins ADD COLUMN about TEXT")
        if "avatar_url" not in existing_columns:
            statements.append("ALTER TABLE admins ADD COLUMN avatar_url VARCHAR(500)")
        if "extra_permissions" not in existing_columns:
            statements.append("ALTER TABLE admins ADD COLUMN extra_permissions TEXT")
        if statements:
            with engine.begin() as connection:
                for statement in statements:
                    connection.execute(text(statement))

    if "media_assets" in inspector.get_table_names():
        existing_columns = {column["name"] for column in inspector.get_columns("media_assets")}
        statements = []
        if "storage_provider" not in existing_columns:
            statements.append("ALTER TABLE media_assets ADD COLUMN storage_provider VARCHAR(100)")
        if "storage_object_key" not in existing_columns:
            statements.append("ALTER TABLE media_assets ADD COLUMN storage_object_key VARCHAR(1024)")
        if "source_url" not in existing_columns:
            statements.append("ALTER TABLE media_assets ADD COLUMN source_url VARCHAR(2048)")
        if "source_label" not in existing_columns:
            statements.append("ALTER TABLE media_assets ADD COLUMN source_label VARCHAR(255)")
        if "uploaded_by_system" not in existing_columns:
            statements.append("ALTER TABLE media_assets ADD COLUMN uploaded_by_system BOOLEAN NOT NULL DEFAULT FALSE")
        if statements:
            with engine.begin() as connection:
                for statement in statements:
                    connection.execute(text(statement))

    if "report_tickets" in inspector.get_table_names():
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE report_tickets ALTER COLUMN tg_user_id TYPE BIGINT"))
            connection.execute(text("ALTER TABLE report_tickets ALTER COLUMN tg_chat_id TYPE BIGINT"))

    if "report_messages" in inspector.get_table_names():
        existing_columns = {column["name"] for column in inspector.get_columns("report_messages")}
        if "tg_user_id" in existing_columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE report_messages ALTER COLUMN tg_user_id TYPE BIGINT"))

    # achievements tables are created by metadata.create_all(); nothing else required here.


def init_database() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    settings.public_upload_dir.mkdir(parents=True, exist_ok=True)
    settings.avatar_upload_dir.mkdir(parents=True, exist_ok=True)
    _ensure_runtime_schema()


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
