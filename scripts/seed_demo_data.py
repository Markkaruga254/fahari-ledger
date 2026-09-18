"""
Create a deterministic, repeatable Fahari Ledger demo scenario.

    python -m scripts.seed_demo_data
    python -m scripts.seed_demo_data --reset

The seed is database-only: it does NOT send SMS or trigger external APIs.
It creates the exact state used by the live demo:
- 30kg tilapia purchased
- 13kg sold for KES 7,800
- 17kg remaining
- KES 2,000 outstanding customer debt
- one pending KES 4,200 hotel invoice with a 29-day deadline
"""
import argparse
from datetime import datetime, timedelta

from app.db.models import Debt, Invoice, Purchase, Sale, Vendor
from app.db.session import Base, engine, SessionLocal
from app.services import ledger

DEMO_VENDOR_PHONE = "+254700000000"
DEMO_CUSTOMER_PHONE = "+254711111111"
DEMO_BUYER = "Nyali Hotel Supplies"


def _demo_event_times(now: datetime) -> dict[str, datetime]:
    business_day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return {
        "purchase": business_day_start + timedelta(hours=8),
        "sale_one": business_day_start + timedelta(hours=11),
        "sale_two": business_day_start + timedelta(hours=13),
        "debt": business_day_start + timedelta(hours=14),
    }


def _reset_demo_vendor(db):
    vendor = (
        db.query(Vendor)
        .filter(Vendor.phone_number == DEMO_VENDOR_PHONE)
        .first()
    )
    if vendor is None:
        return

    db.query(Purchase).filter(Purchase.vendor_id == vendor.id).delete(
        synchronize_session=False
    )
    db.query(Sale).filter(Sale.vendor_id == vendor.id).delete(
        synchronize_session=False
    )
    db.query(Debt).filter(Debt.vendor_id == vendor.id).delete(
        synchronize_session=False
    )
    db.query(Invoice).filter(Invoice.vendor_id == vendor.id).delete(
        synchronize_session=False
    )
    db.delete(vendor)
    db.commit()


def run(reset: bool = False):
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        if reset:
            _reset_demo_vendor(db)

        existing = (
            db.query(Vendor)
            .filter(Vendor.phone_number == DEMO_VENDOR_PHONE)
            .first()
        )
        if existing is not None:
            print(
                f"Demo vendor {DEMO_VENDOR_PHONE} already exists. "
                "Use --reset to rebuild the scenario."
            )
            return

        # Anchor to business-day start so all demo events stay within one day.
        now = datetime.utcnow()
        event_times = _demo_event_times(now)

        purchase = ledger.log_purchase(
            db, DEMO_VENDOR_PHONE, "tilapia", quantity=30, cost=12000
        )
        purchase.created_at = event_times["purchase"]

        sale_one = ledger.log_sale(
            db, DEMO_VENDOR_PHONE, "tilapia", quantity=8, price=4800
        )
        sale_one.created_at = event_times["sale_one"]

        sale_two = ledger.log_sale(
            db, DEMO_VENDOR_PHONE, "tilapia", quantity=5, price=3000
        )
        sale_two.created_at = event_times["sale_two"]

        debt = ledger.log_debt(
            db,
            DEMO_VENDOR_PHONE,
            DEMO_CUSTOMER_PHONE,
            "tilapia",
            2000,
            notify_customer=False,
        )
        debt.created_at = event_times["debt"]

        invoice = ledger.create_invoice(
            db,
            DEMO_VENDOR_PHONE,
            DEMO_BUYER,
            4200,
            deadline_days=29,
        )

        # The ledger helpers commit each event. Persist the demo timestamps and
        # leave the invoice creation timestamp as the actual rehearsal time.
        db.commit()

        print(f"Demo scenario ready for {DEMO_VENDOR_PHONE}")
        print("  Purchase: 30kg tilapia / KES 12,000")
        print("  Sales:    8kg + 5kg / KES 7,800 total")
        print("  Remaining:17kg tilapia")
        print("  Debt:     KES 2,000")
        print(f"  Invoice:  KES 4,200 from {invoice.buyer_name} / 29 days")
        print("")
        print("Next:")
        print("  1. Walk the USSD flow with the demo phone.")
        print("  2. Trigger the overstock SMS when the scheduler runs.")
        print("  3. Use trigger_etims_event for a fresh invoice alert if needed.")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Seed the Fahari demo scenario.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete and rebuild the demo vendor's data.",
    )
    args = parser.parse_args()
    run(reset=args.reset)


if __name__ == "__main__":
    main()
