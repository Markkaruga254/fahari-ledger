from html import escape

from fastapi import APIRouter, Form
from fastapi.responses import Response

from app.config import settings
from app.db.session import SessionLocal
from app.services import ledger
from app.services import notifications
from app.voice.asr_client import transcribe
from app.voice.item_parser import parse_transcript

router = APIRouter()


def _recording_callback_url() -> str:
    base = settings.public_base_url.rstrip("/")
    return f"{base}/voice/recording" if base else "/voice/recording"


def _voice_xml(message: str) -> Response:
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Say>{escape(message)}</Say></Response>"
    )
    return Response(content=body, media_type="application/xml")


@router.post("/voice", response_class=Response)
async def voice_callback(
    phoneNumber: str = Form(""),
    isActive: str = Form("1"),
    callerNumber: str = Form(""),
):
    callback_url = escape(_recording_callback_url(), quote=True)
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        '<Say voice="woman">Tell me what you sold. For example, kilo mbili za nyanya, bei mia moja.</Say>'
        f'<Record finishOnKey="#" maxLength="15" trimSilence="true" playBeep="true" '
        f'callbackUrl="{callback_url}"/>'
        "</Response>"
    )
    return Response(content=body, media_type="application/xml")


@router.post("/voice/recording", response_class=Response)
async def voice_recording_callback(
    phoneNumber: str = Form(""),
    recordingUrl: str = Form(""),
    callerNumber: str = Form(""),
):
    # Africa's Talking identifies the caller as `callerNumber` on voice
    # callbacks; `phoneNumber` is accepted too so sandbox/simulator posts
    # shaped like the USSD callback keep working. Either way we must never
    # 422 on a real call — a missing field degrades to a spoken fallback.
    caller = phoneNumber or callerNumber
    if not caller:
        return _voice_xml("Sorry, I could not identify your number. Please dial the USSD code instead.")

    transcript = transcribe(recordingUrl) if recordingUrl else None
    if not transcript:
        return _voice_xml("Sorry, I could not hear that. Please dial the USSD code instead.")

    parsed = parse_transcript(transcript)
    if (
        not parsed
        or parsed.get("price") is None
        or (parsed.get("quantity") or 0) <= 0
        or (parsed.get("price") or 0) <= 0
    ):
        return _voice_xml("I did not catch the full details. Please try the USSD code instead.")

    db = SessionLocal()
    try:
        ledger.log_sale(
            db,
            caller,
            parsed["item"],
            parsed["quantity"],
            parsed["price"],
            source="voice",
        )
    except ValueError:
        return _voice_xml("I did not catch the full details. Please try the USSD code instead.")
    finally:
        db.close()

    notifications.send_voice_sale_confirmation(
        caller,
        parsed["item"],
        parsed["quantity"],
        parsed["price"],
    )

    confirmation = (
        f"Confirmed: sold {parsed['quantity']:g} {parsed['item']} "
        f"for {parsed['price']:.0f} shillings. I also sent an SMS confirmation."
    )
    return _voice_xml(confirmation)
