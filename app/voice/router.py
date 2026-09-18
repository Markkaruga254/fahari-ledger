from fastapi import APIRouter, Form
from fastapi.responses import PlainTextResponse

from app.db.session import SessionLocal
from app.services import ledger
from app.services import notifications
from app.voice.asr_client import transcribe
from app.voice.item_parser import parse_transcript

router = APIRouter()

_VOICE_XML_PROMPT = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    "<Response>"
    '<Say voice="woman">Tell me what you sold. For example, kilo mbili za nyanya, bei mia moja.</Say>'
    '<Record finishOnKey="#" maxLength="15" trimSilence="true" playBeep="true" '
    'callbackUrl="/voice/recording"/>'
    "</Response>"
)


@router.post("/voice", response_class=PlainTextResponse)
async def voice_callback(phoneNumber: str = Form(...), isActive: str = Form("1")):
    return _VOICE_XML_PROMPT


@router.post("/voice/recording", response_class=PlainTextResponse)
async def voice_recording_callback(phoneNumber: str = Form(...), recordingUrl: str = Form(...)):
    transcript = transcribe(recordingUrl)
    if not transcript:
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Response><Say>Sorry, I could not hear that. Please dial the USSD code instead.</Say></Response>'
        )

    parsed = parse_transcript(transcript)
    if not parsed or parsed.get("price") is None:
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Response><Say>I did not catch the full details. Please try the USSD code instead.</Say></Response>'
        )

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
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Say>{confirmation}</Say></Response>"
    )
