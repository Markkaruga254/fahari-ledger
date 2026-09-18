"""
In-memory USSD session state. Fine for a hackathon demo (single process);
swap for Redis if you ever run more than one app instance.
"""
from typing import Any

_SESSIONS: dict[str, dict[str, Any]] = {}


def get_session(session_id: str) -> dict:
    return _SESSIONS.setdefault(session_id, {"state": "MAIN_MENU", "data": {}})


def clear_session(session_id: str) -> None:
    _SESSIONS.pop(session_id, None)
