from fastapi import APIRouter, Form
from fastapi.responses import PlainTextResponse

from app.ussd import menus
from app.ussd.session import get_session

router = APIRouter()


@router.post("/ussd", response_class=PlainTextResponse)
async def ussd_callback(
    sessionId: str = Form(...),
    serviceCode: str = Form(...),
    phoneNumber: str = Form(...),
    text: str = Form(""),
):
    session = get_session(sessionId)
    session["phone_number"] = phoneNumber
    response_text, _ = menus.handle(sessionId, phoneNumber, text)
    return response_text
