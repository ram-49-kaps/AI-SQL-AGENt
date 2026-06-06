"""
Database module — connection management, schema introspection, and query execution.

Provides:
    - SQLAlchemy engine and session factory for SQLite
    - Database initialization (schema + seed) on first run
    - Safe read-only query execution
    - Dynamic schema introspection for LLM context
"""

import os
import logging
import sqlite3
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

logger = logging.getLogger(__name__)

# ─── Base class for ORM models ───────────────────────────────────
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# ─── Paths ───────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "company.db"
SCHEMA_FILE = DATA_DIR / "schema.sql"
SEED_FILE = DATA_DIR / "seed.sql"


# ─── Engine & Session ────────────────────────────────────────────
def _build_database_url() -> str:
    """Build the database URL, ensuring absolute paths for SQLite."""
    url = os.getenv("DATABASE_URL", "")
    if url and url != "sqlite:///data/company.db":
        return url
    # Always use absolute path for SQLite
    return f"sqlite:///{DB_PATH}"

DATABASE_URL = _build_database_url()

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency — yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Database Initialization ────────────────────────────────────
def init_db() -> None:
    """
    Initialize the database by running schema.sql and seed.sql.

    Uses raw sqlite3 for DDL execution since SQLAlchemy's
    text() doesn't handle multi-statement scripts cleanly.
    Idempotent — safe to call multiple times.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Initializing database at %s", DB_PATH)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Enable foreign key enforcement
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Run schema
    if SCHEMA_FILE.exists():
        schema_sql = SCHEMA_FILE.read_text()
        cursor.executescript(schema_sql)
        logger.info("Schema applied from %s", SCHEMA_FILE)
    else:
        logger.warning("Schema file not found: %s", SCHEMA_FILE)

    # Run seed data
    if SEED_FILE.exists():
        seed_sql = SEED_FILE.read_text()
        cursor.executescript(seed_sql)
        logger.info("Seed data applied from %s", SEED_FILE)
    else:
        logger.warning("Seed file not found: %s", SEED_FILE)

    conn.commit()
    conn.close()

    logger.info("Database initialization complete.")


# ─── Query Execution ────────────────────────────────────────────
def execute_query(sql: str) -> list[dict[str, Any]]:
    """
    Execute a read-only SQL query and return results as a list of dicts.

    Args:
        sql: The SQL SELECT statement to execute.

    Returns:
        List of dictionaries, one per row, with column names as keys.

    Raises:
        Exception: If the query fails (caught upstream by agent).
    """
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        columns = list(result.keys())
        rows = result.fetchall()

        return [dict(zip(columns, row)) for row in rows]


# ─── Schema Introspection ───────────────────────────────────────
def get_schema_info() -> str:
    """
    Dynamically inspect the database and return a formatted schema
    string suitable for LLM context.

    Returns:
        A human-readable schema description including table names,
        column names, types, primary keys, and foreign keys.
    """
    inspector = inspect(engine)
    schema_parts: list[str] = []

    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        pk_cols = inspector.get_pk_constraint(table_name)
        fk_list = inspector.get_foreign_keys(table_name)

        # Table header
        lines = [f"TABLE: {table_name}"]
        lines.append("  Columns:")

        for col in columns:
            col_info = f"    - {col['name']} ({col['type']})"
            if col["name"] in (pk_cols.get("constrained_columns") or []):
                col_info += " [PRIMARY KEY]"
            if not col.get("nullable", True):
                col_info += " [NOT NULL]"
            lines.append(col_info)

        # Foreign keys
        if fk_list:
            lines.append("  Foreign Keys:")
            for fk in fk_list:
                src = ", ".join(fk["constrained_columns"])
                ref_table = fk["referred_table"]
                ref_cols = ", ".join(fk["referred_columns"])
                lines.append(f"    - {src} → {ref_table}({ref_cols})")

        schema_parts.append("\n".join(lines))

    return "\n\n".join(schema_parts)


def get_row_counts() -> dict[str, int]:
    """Return row counts for all tables — useful for context."""
    inspector = inspect(engine)
    counts = {}
    with engine.connect() as conn:
        for table_name in inspector.get_table_names():
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            counts[table_name] = result.scalar()
    return counts
