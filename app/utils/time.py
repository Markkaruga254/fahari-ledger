"""UTC clock helpers used by the ledger and notification layers."""
from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current UTC time as a naive datetime.

    The database schema currently uses SQLAlchemy DateTime without timezone,
    so we keep the stored representation UTC-naive while using the modern
    timezone-aware clock API internally.
    """
    return datetime.now(UTC).replace(tzinfo=None)
