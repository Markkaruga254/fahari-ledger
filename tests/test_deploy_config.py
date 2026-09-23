"""
Deployment-config tests: database URL normalization.

Render issues Postgres URLs in the `postgres://` scheme, which the pinned
SQLAlchemy (2.0.35) rejects. `normalize_database_url` must convert them to
`postgresql://` while leaving every other URL untouched.
"""
from sqlalchemy import create_engine

from app.db.session import normalize_database_url


def test_postgres_scheme_is_converted():
    assert (
        normalize_database_url("postgres://u:p@host:5432/db")
        == "postgresql://u:p@host:5432/db"
    )


def test_postgresql_scheme_passes_through():
    url = "postgresql://fahari:fahari@db:5432/fahari_ledger"
    assert normalize_database_url(url) == url


def test_sqlite_url_passes_through():
    assert normalize_database_url("sqlite://") == "sqlite://"


def test_converted_url_is_accepted_by_pinned_sqlalchemy():
    engine = create_engine(
        normalize_database_url("postgres://u:p@host:5432/db")
    )
    assert engine.url.drivername == "postgresql"
    engine.dispose()


def test_whitespace_is_stripped():
    assert (
        normalize_database_url("  postgresql://h/db  ")
        == "postgresql://h/db"
    )
