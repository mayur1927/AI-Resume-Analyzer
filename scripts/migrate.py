"""Standalone database migration and schema initialization script.

Use this script to initialize or migrate the PostgreSQL schema for local development
or production hosted databases (e.g. Neon, Supabase, AWS RDS, Render PostgreSQL).

Usage:
    python scripts/migrate.py
"""

import logging
import os
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from sqlalchemy import inspect, text
from backend.database import Base, get_database_url, get_engine
from backend.models import Analysis

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("migration")


def run_migrations():
    """Run database schema migrations against the target database."""
    db_url = get_database_url()
    if not db_url:
        logger.error(
            "DATABASE_URL environment variable is not set. "
            "Please configure your connection string in .env (local) or environment variables (production)."
        )
        sys.exit(1)

    # Safe display of target host without exposing credentials
    masked_url = db_url.split("@")[-1] if "@" in db_url else "configured database"
    logger.info(f"Connecting to database host: {masked_url}...")

    try:
        engine = get_engine()
        inspector = inspect(engine)

        existing_tables = inspector.get_table_names()
        logger.info(f"Existing tables in database: {existing_tables or 'None'}")

        if "analyses" not in existing_tables:
            logger.info("Table 'analyses' does not exist. Creating schema...")
            Base.metadata.create_all(bind=engine)
            logger.info("Successfully created 'analyses' table and associated constraints.")
        else:
            logger.info("Table 'analyses' already exists.")
            columns = [col["name"] for col in inspector.get_columns("analyses")]
            logger.info(f"Verified columns in 'analyses': {columns}")

        # Ensure index on created_at for fast sorting / analytics
        with engine.begin() as conn:
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses (created_at DESC);")
            )
            logger.info("Verified index 'idx_analyses_created_at'.")

        logger.info("All database migrations completed successfully!")

    except Exception as exc:
        logger.error(f"Database migration failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    run_migrations()
