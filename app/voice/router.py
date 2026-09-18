from html import escape

from fastapi import APIRouter, Form
from fastapi.responses import PlainTextResponse

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


def _voice_xml(message: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Say>{escape(message)}</Say></Response>"
    )


@router.post("/voice", response_class=PlainTextResponse)
async def voice_callback(phoneNumber: str = Form(...), isActive: str = Form("1")):
    callback_url = escape(_recording_callback_url(), quote=True)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        '<Say voice="woman">Tell me what you sold. For example, kilo mbili za nyanya, bei mia moja.</Say>'
        f'<Record finishOnKey="#" maxLength="15" trimSilence="true" playBeep="true" '
        f'callbackUrl="{callback_url}"/>'
        "</Response>"
    )


@router.post("/voice/recording", response_class=PlainTextResponse)
async def voice_recording_callback(phoneNumber: str = Form(...), recordingUrl: str = Form(...)):
    transcript = transcribe(recordingUrl)
    if not transcript:
        return _voice_xml("Sorry, I could not hear that. Please dial the USSD code instead.")

    parsed = parse_transcript(transcript)
    if not parsed or parsed.get("price") is None:
        return _voice_xml("I did not catch the full details. Please try the USSD code instead.")

    db = SessionLocal()
    try:
        ledger.log_sale(
            db,
            phoneNumber,
            parsed["item"],
            parsed["quantity"],
            parsed["price"],
            source="voice",
        )
    finally:
        db.close()

    notifications.send_voice_sale_confirmation(
        phoneNumber,
        parsed["item"],
        parsed["quantity"],
        parsed["price"],
    )

    confirmation = (
        f"Confirmed: sold {parsed['quantity']:g} {parsed['item']} "
        f"for {parsed['price']:.0f} shillings. I also sent an SMS confirmation."
    )
    return _voice_xml(confirmation)
