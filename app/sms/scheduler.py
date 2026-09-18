"""
Two background jobs:
  - overstock check: periodically scans open stock per vendor/item and fires
    the nudge SMS once per threshold breach.
  - end-of-day summary: fires once per vendor at a fixed hour.

Kept deliberately simple (APScheduler, in-process) for the hackathon build.
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
            for item, sold_qty in summary["items_sold"].items():
                purchased_qty = ledger.stock_remaining(db, vendor.id, item, today_start) + sold_qty
                remaining = purchased_qty - sold_qty
                if overstock.should_nudge(purchased_qty, sold_qty):
                    send_sms(vendor.phone_number, templates.overstock_nudge(item, remaining))
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
                summary["total_sales"], summary["total_owed_to_vendor"], summary["sale_count"], pending
            )
            send_sms(vendor.phone_number, msg)
    finally:
        db.close()


def start_scheduler():
    if not _scheduler.running:
        _scheduler.add_job(check_overstock_job, "interval", minutes=30, id="overstock_check")
        _scheduler.add_job(send_eod_summaries_job, "cron", hour=19, minute=0, id="eod_summary")
        _scheduler.start()
