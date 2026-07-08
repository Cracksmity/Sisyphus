from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./sysiphus.db"

# connect_args={"check_same_thread": False} is needed only for SQLite. It's not needed for other databases.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_sqlite_schema() -> None:
    """
    Lightweight schema patching for local SQLite runs without Alembic.
    Safe no-op for columns that already exist.
    """
    schema_updates = {
        "projects": [
            ("owner_id", "TEXT"),
        ],
        "guided_states": [
            ("stage_idea", "TEXT DEFAULT ''"),
            ("stage_estructura", "TEXT DEFAULT ''"),
            ("stage_introduccion", "TEXT DEFAULT ''"),
            ("stage_desarrollo", "TEXT DEFAULT ''"),
            ("stage_contraargumento", "TEXT DEFAULT ''"),
            ("stage_conclusion", "TEXT DEFAULT ''"),
        ],
        "interactions": [
            ("model_used", "TEXT DEFAULT ''"),
            ("fallback_used", "INTEGER DEFAULT 0"),
            ("prompt_tokens_estimate", "INTEGER DEFAULT 0"),
            ("completion_tokens_estimate", "INTEGER DEFAULT 0"),
            ("total_tokens_estimate", "INTEGER DEFAULT 0"),
            ("context_chars", "INTEGER DEFAULT 0"),
        ],
        "essay_memories": [
            ("map_summary", "TEXT DEFAULT ''"),
            ("global_summary", "TEXT DEFAULT ''"),
            ("summary_status", "TEXT DEFAULT 'idle'"),
            ("summary_error", "TEXT DEFAULT ''"),
            ("summary_hash", "TEXT DEFAULT ''"),
            ("rag_status", "TEXT DEFAULT 'idle'"),
            ("rag_error", "TEXT DEFAULT ''"),
            ("rag_hash", "TEXT DEFAULT ''"),
        ],
    }

    with engine.begin() as conn:
        for table_name, columns in schema_updates.items():
            existing_columns = {
                row[1] for row in conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
            }
            for col_name, col_type in columns:
                if col_name in existing_columns:
                    continue
                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
