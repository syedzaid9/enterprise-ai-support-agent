"""
Database connection and session management for ResolveAI.
Supports PostgreSQL as primary production DB, with automatic SQLite fallback for zero-config local development.
"""

import logging
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import DATABASE_URL

logger = logging.getLogger("resolveai.database")

Base = declarative_base()


def _init_engine():
    """
    Initialize SQLAlchemy engine. If the configured PostgreSQL database is unreachable,
    automatically falls back to local SQLite to ensure zero-crash development.
    """
    target_url = DATABASE_URL
    connect_args = {}

    if target_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        return create_engine(target_url, connect_args=connect_args), target_url

    # Attempt PostgreSQL connection
    try:
        eng = create_engine(
            target_url,
            connect_args=connect_args,
            pool_pre_ping=True,
        )
        # Test connection immediately
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return eng, target_url
    except Exception as exc:
        logger.warning(
            f"Primary database connection to '{target_url}' failed: {exc}. "
            "Falling back to local SQLite database ('sqlite:///resolveai.db')."
        )
        fallback_url = "sqlite:///resolveai.db"
        eng = create_engine(fallback_url, connect_args={"check_same_thread": False})
        return eng, fallback_url


engine, ACTIVE_DATABASE_URL = _init_engine()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    Automatically handles commit/rollback and closes the session.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    Initialize database tables defined in models and synchronize missing columns.
    """
    from sqlalchemy import inspect
    import app.db.models  # Ensure models are imported and registered with Base

    Base.metadata.create_all(bind=engine)

    # Automatically synchronize any newly added model columns to existing tables
    try:
        inspector = inspect(engine)
        with engine.connect() as conn:
            for table_name, table in Base.metadata.tables.items():
                if not inspector.has_table(table_name):
                    continue
                existing_columns = {col["name"] for col in inspector.get_columns(table_name)}
                for col in table.columns:
                    if col.name not in existing_columns:
                        col_type = col.type.compile(engine.dialect)
                        sql = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}"
                        try:
                            conn.execute(text(sql))
                            conn.commit()
                        except Exception as e:
                            logger.debug(f"Column add skipped for {table_name}.{col.name}: {e}")
    except Exception as exc:
        logger.debug(f"Schema synchronization check completed: {exc}")


