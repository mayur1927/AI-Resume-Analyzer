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
from backend.models import Analysis, ResumeOptimization

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

        # 1. analyses table
        if "analyses" not in existing_tables:
            logger.info("Table 'analyses' does not exist. Creating schema...")
            Base.metadata.create_all(bind=engine)
            logger.info("Successfully created database tables and associated constraints.")
        else:
            logger.info("Table 'analyses' already exists.")
            columns = [col["name"] for col in inspector.get_columns("analyses")]
            logger.info(f"Existing columns in 'analyses': {columns}")

            # Idempotently add owner_id column if missing from legacy schema
            if "owner_id" not in columns:
                logger.info("Adding 'owner_id' column to 'analyses'...")
                with engine.begin() as conn:
                    conn.execute(
                        text("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS owner_id UUID;")
                    )
                    # Assign legacy records to a deterministic legacy owner ID
                    conn.execute(
                        text(
                            "UPDATE analyses SET owner_id = '00000000-0000-0000-0000-000000000000' "
                            "WHERE owner_id IS NULL;"
                        )
                    )
                    conn.execute(
                        text("ALTER TABLE analyses ALTER COLUMN owner_id SET NOT NULL;")
                    )
                logger.info("Successfully added 'owner_id' column and backfilled legacy records.")

        # Ensure performance and isolation indexes exist for analyses
        with engine.begin() as conn:
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_analyses_owner_id ON analyses (owner_id);")
            )
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_analyses_owner_created ON analyses (owner_id, created_at DESC);")
            )
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses (created_at DESC);")
            )
            logger.info("Verified isolation and sorting indexes for 'analyses'.")

        # 2. optimizations table
        # Refresh existing tables
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        if "optimizations" not in existing_tables:
            logger.info("Table 'optimizations' does not exist. Creating 'optimizations' schema...")
            ResumeOptimization.__table__.create(bind=engine)
            logger.info("Successfully created 'optimizations' table.")
        else:
            logger.info("Table 'optimizations' already exists.")

        # Ensure performance and isolation indexes exist for optimizations
        with engine.begin() as conn:
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_optimizations_owner_id ON optimizations (owner_id);")
            )
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_optimizations_owner_created ON optimizations (owner_id, created_at DESC);")
            )
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_optimizations_created_at ON optimizations (created_at DESC);")
            )
            logger.info("Verified isolation and sorting indexes for 'optimizations'.")

        logger.info("All database migrations completed successfully!")

    except Exception as exc:
        logger.error(f"Database migration failed: {exc}")
        sys.exit(1)



if __name__ == "__main__":
    run_migrations()
