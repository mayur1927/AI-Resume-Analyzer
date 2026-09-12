"""Database connection and SQLAlchemy session helpers with serverless compatibility."""

import logging
import os
from typing import Generator, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

load_dotenv()
logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class used by every database table."""
    pass


def get_database_url() -> str:
    """Retrieve and normalize the PostgreSQL connection URL."""
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        return ""

    # Standardize cloud PostgreSQL URLs (e.g. Render, Supabase, Neon) for psycopg3
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and "+psycopg" not in url and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)

    return url


_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def is_serverless_environment() -> bool:
    """Detect if running in a serverless cloud environment (e.g. Vercel / AWS Lambda)."""
    return bool(
        os.getenv("VERCEL")
        or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
        or os.getenv("SERVERLESS")
    )


def get_engine() -> Engine:
    """Lazily create and return the SQLAlchemy engine with serverless-optimized pooling."""
    global _engine, _SessionLocal
    if _engine is not None:
        return _engine

    db_url = get_database_url()
    if not db_url:
        raise RuntimeError(
            "DATABASE_URL is not configured. Please set the DATABASE_URL environment variable."
        )

    # Serverless-friendly connection parameters
    connect_args = {}
    is_local = "localhost" in db_url or "127.0.0.1" in db_url

    if not is_local:
        # Enforce SSL requirement for remote cloud database providers (e.g., Neon, Supabase)
        if "sslmode" not in db_url.lower():
            connect_args["sslmode"] = "require"

    if is_serverless_environment():
        # In serverless functions, avoid holding idle connections open in frozen containers
        _engine = create_engine(
            db_url,
            poolclass=NullPool,
            connect_args=connect_args,
        )
    else:
        # Standard local development / persistent server connection pool
        _engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=5,
            max_overflow=10,
            connect_args=connect_args,
        )

    _SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
    return _engine


def get_sessionmaker() -> sessionmaker:
    """Get the sessionmaker factory."""
    global _SessionLocal
    if _SessionLocal is None:
        get_engine()
    assert _SessionLocal is not None
    return _SessionLocal


def init_db():
    """Ensure database tables and schema modifications exist (safe runtime fallback)."""
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        # Verify and idempotently patch owner_id and indexes
        with engine.begin() as conn:
            conn.exec_driver_sql("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS owner_id UUID;")
            conn.exec_driver_sql(
                "UPDATE analyses SET owner_id = '00000000-0000-0000-0000-000000000000' WHERE owner_id IS NULL;"
            )
            conn.exec_driver_sql("ALTER TABLE analyses ALTER COLUMN owner_id SET NOT NULL;")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS idx_analyses_owner_id ON analyses (owner_id);")
            conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS idx_analyses_owner_created ON analyses (owner_id, created_at DESC);"
            )
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses (created_at DESC);")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS idx_optimizations_owner_id ON optimizations (owner_id);")
            conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS idx_optimizations_owner_created ON optimizations (owner_id, created_at DESC);"
            )
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS idx_optimizations_created_at ON optimizations (created_at DESC);")
        logger.info("Database schema verified.")
    except Exception as exc:
        logger.warning(f"Database schema verification deferred: {exc}")



def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a request-scoped database session."""
    session_factory = get_sessionmaker()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
