from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings


def normalize_database_url(url: str) -> str:
    """Return a SQLAlchemy-connectable URL for a Postgres connection string.

    Managed providers (Render included) commonly issue URLs in the
    `postgres://` scheme, which this repository's pinned SQLAlchemy (2.0.35)
    rejects with `NoSuchModuleError: Can't load plugin:
    sqlalchemy.dialects:postgres` (reproduced in the app container).
    The wire protocol is identical; only the scheme prefix differs.
    Non-Postgres URLs (e.g. `sqlite://` used by tests) pass through
    untouched.
    """
    cleaned = url.strip()
    if cleaned.startswith("postgres://"):
        return "postgresql://" + cleaned[len("postgres://"):]
    return cleaned


engine = create_engine(normalize_database_url(settings.database_url), future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
