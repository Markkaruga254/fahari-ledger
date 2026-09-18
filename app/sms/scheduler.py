"""
Background notification jobs.

The scheduler derives stock from the ledger rather than reconstructing it from
only sold items. A vendor can therefore receive an overstock alert even when
an item has been purchased but has not sold yet.
"""
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import SessionLocal
from app.db.models import Vendor
from app.services import ledger, overstock
from app.sms import templates
from app.sms.sender import send_sms

_scheduler = BackgroundScheduler()


def check_overstock_job():
    db = SessionLocal()
    try:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        for vendor in db.query(Vendor).all():
            summary = ledger.today_summary(db, vendor.id)

            for item, purchased_qty in summary["items_purchased"].items():
                sold_qty = summary["items_sold"].get(item, 0.0)
                remaining = max(purchased_qty - sold_qty, 0.0)

                if overstock.should_nudge(purchased_qty, sold_qty):
                    send_sms(
                        vendor.phone_number,
                        templates.overstock_nudge(item, remaining),
                    )
    finally:
        db.close()


def send_eod_summaries_job():
    db = SessionLocal()
    try:
        for vendor in db.query(Vendor).all():
            summary = ledger.today_summary(db, vendor.id)
            pending = len(ledger.pending_invoices(db, vendor.id))
            has_stock_activity = any(qty > 0 for qty in summary["items_purchased"].values()) or any(
                qty > 0 for qty in summary["items_remaining"].values()
            )

            if summary["sale_count"] == 0 and pending == 0 and not has_stock_activity:
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
