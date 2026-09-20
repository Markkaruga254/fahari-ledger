import asyncio

from app.sms.router import sms_delivery_status


def test_sms_delivery_status_returns_ok_and_logs(caplog):
    caplog.set_level("INFO", logger="fahari.sms.status")

    response = asyncio.run(
        sms_delivery_status(
            id="ATXid_123",
            status="Success",
            phoneNumber="+254700000000",
            networkCode="63902",
            failureReason="",
        )
    )

    assert response == "OK"
    assert "ATXid_123" in caplog.text
    assert "+254700000000" in caplog.text


def test_sms_delivery_status_handles_missing_fields():
    response = asyncio.run(sms_delivery_status())

    assert response == "OK"
