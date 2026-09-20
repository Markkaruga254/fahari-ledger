import logging
import time

from app.utils.at_client import sms as at_sms
from app.config import settings

logger = logging.getLogger("fahari.sms")

# Kept small and module-level (not settings) on purpose: this is retry
# policy for one adapter call, not a product-configurable knob. Tests
# monkeypatch _BACKOFF_SECONDS to 0 to run instantly.
_MAX_ATTEMPTS = 3
_BACKOFF_SECONDS = 0.2


def send_sms(to: str, message: str) -> dict:
    """Thin wrapper over the AT SMS SDK.

    Retries a transient failure (e.g. a dropped connection to AT) up to
    `_MAX_ATTEMPTS` times with a short linear backoff, then swallows and logs
    so a failed SMS never takes down the caller's request (a USSD session,
    the overstock/EOD scheduler, or the voice confirmation path). Callers get
    back the AT SDK's response dict, or `{"error": ...}` once every attempt
    has failed.
    """
    last_error: Exception | None = None

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            return at_sms.send(message, [to], settings.at_sender_id)
        except Exception as exc:  # pragma: no cover - network dependent
            last_error = exc
            logger.warning(
                "sms send attempt %s/%s to %s failed: %s",
                attempt, _MAX_ATTEMPTS, to, exc,
            )
            if attempt < _MAX_ATTEMPTS:
                time.sleep(_BACKOFF_SECONDS * attempt)

    logger.error(
        "sms send to %s failed after %s attempts: %s",
        to, _MAX_ATTEMPTS, last_error,
    )
    return {"error": str(last_error)}
