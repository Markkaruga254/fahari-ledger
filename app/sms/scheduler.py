"""Background notification jobs for SMS-based business nudges.

The scheduler derives stock from the ledger rather than reconstructing it from
only sold items. A vendor can therefore receive an overstock alert even when
an item has been purchased but has not sold yet.
"""
from app.utils.time import utc_now

from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import SessionLocal
from app.db.models import Vendor
from app.services import ledger, overstock
from app.sms import templates
from app.sms.sender import send_sms

_scheduler = BackgroundScheduler()

# The scheduler runs every 30 minutes, so keep one alert per vendor/item/day.
# This is intentionally lightweight for the single-process hackathon deployment.
_sent_overstock_alerts: set[tuple[int, str, str]] = set()


def reset_overstock_alerts() -> None:
    """Clear in-process alert state; useful for tests and demo resets."""
    _sent_overstock_alerts.clear()


def check_overstock_job():
    db = SessionLocal()
    try:
        today = utc_now().date().isoformat()

        for vendor in db.query(Vendor).all():
            summary = ledger.today_summary(db, vendor.id)

            for item, purchased_qty in summary["items_purchased"].items():
                sold_qty = summary["items_sold"].get(item, 0.0)
                remaining = max(purchased_qty - sold_qty, 0.0)
                alert_key = (vendor.id, item, today)

                if alert_key in _sent_overstock_alerts:
                    continue

                if overstock.should_nudge(purchased_qty, sold_qty):
                    send_sms(
                        vendor.phone_number,
                        templates.overstock_nudge(item, remaining),
                    )
                    _sent_overstock_alerts.add(alert_key)
    finally:
        db.close()


def send_eod_summaries_job():
    db = SessionLocal()
    try:
        for vendor in db.query(Vendor).all():
            summary = ledger.today_summary(db, vendor.id)
            pending = len(ledger.pending_invoices(db, vendor.id))

            if summary["sale_count"] == 0 and pending == 0:
                continue

            msg = templates.end_of_day_summary(
                summary["total_sales"],
                summary["total_owed_to_vendor"],
                summary["sale_count"],
                pending,
                summary["items_remaining"],
            )
            send_sms(vendor.phone_number, msg)
    finally:
        db.close()


def start_scheduler():
    if not _scheduler.running:
        _scheduler.add_job(
            check_overstock_job,
            "interval",
            minutes=30,
            id="overstock_check",
            replace_existing=True,
        )
        _scheduler.add_job(
            send_eod_summaries_job,
            "cron",
            hour=19,
            minute=0,
            id="eod_summary",
            replace_existing=True,
        )
        _scheduler.start()
