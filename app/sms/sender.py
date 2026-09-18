from app.utils.at_client import sms as at_sms
from app.config import settings


def send_sms(to: str, message: str) -> dict:
    """Thin wrapper over the AT SMS SDK. Swallows and logs errors so a failed
    SMS never takes down the caller's request (e.g. a USSD session)."""
    try:
        return at_sms.send(message, [to], settings.at_sender_id)
    except Exception as exc:  # pragma: no cover - network dependent
        print(f"[sms] failed to send to {to}: {exc}")
        return {"error": str(exc)}
