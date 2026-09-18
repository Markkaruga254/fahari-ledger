"""Notification orchestration for Fahari's telecom layer.

Business services decide what happened; this module decides which message
template to send and delegates delivery to the Africa's Talking adapter.
"""

from app.sms import templates
from app.sms.sender import send_sms


def send_debt_reminder(customer_phone: str, amount: float, item: str | None, vendor_name: str = "the seller") -> dict:
    return send_sms(
        customer_phone,
        templates.debt_reminder(vendor_name, amount, item),
    )


def send_overstock_alert(vendor_phone: str, item: str, remaining_qty: float) -> dict:
    return send_sms(
        vendor_phone,
        templates.overstock_nudge(item, remaining_qty),
    )


def send_invoice_alert(vendor_phone: str, buyer_name: str, amount: float, days_left: int) -> dict:
    return send_sms(
        vendor_phone,
        templates.etims_invoice_alert(buyer_name, amount, days_left),
    )


def send_voice_sale_confirmation(vendor_phone: str, item: str, quantity: float, price: float) -> dict:
    return send_sms(
        vendor_phone,
        templates.voice_sale_confirmation(item, quantity, price),
    )


def send_end_of_day_summary(
    vendor_phone: str,
    total_sales: float,
    total_owed: float,
    sale_count: int,
    pending_invoices: int,
    items_remaining: dict[str, float] | None = None,
) -> dict:
    return send_sms(
        vendor_phone,
        templates.end_of_day_summary(
            total_sales,
            total_owed,
            sale_count,
            pending_invoices,
            items_remaining,
        ),
    )
