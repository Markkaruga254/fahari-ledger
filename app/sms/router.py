"""Africa's Talking SMS delivery-report callback.

AT POSTs here (application/x-www-form-urlencoded) once the network has
resolved delivery of a message sent via `app/sms/sender.py`. This is
optional infrastructure: the product does not depend on delivery reports to
function, so this endpoint only logs and always returns 200. It must never
raise, or AT will retry the callback and spam the logs.

Configure the callback URL in the AT dashboard as:
    https://<public-host>/sms/status
"""
import logging

from fastapi import APIRouter, Form
from fastapi.responses import PlainTextResponse

logger = logging.getLogger("fahari.sms.status")

router = APIRouter()


@router.post("/sms/status", response_class=PlainTextResponse)
async def sms_delivery_status(
    id: str = Form(""),
    status: str = Form(""),
    phoneNumber: str = Form(""),
    networkCode: str = Form(""),
    failureReason: str = Form(""),
):
    logger.info(
        "sms delivery report id=%s phone=%s status=%s network=%s failure=%s",
        id, phoneNumber, status, networkCode, failureReason or "-",
    )
    return "OK"
