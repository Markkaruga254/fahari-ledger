"""
Run once before a demo/rehearsal:

    python -m scripts.seed_demo_data

Creates the tables (hackathon speed — no migrations) and seeds one vendor
with a morning purchase, so the live demo starts from a realistic baseline
instead of an empty ledger.
"""
from app.db.session import Base, engine, SessionLocal
from app.services import ledger

DEMO_VENDOR_PHONE = "+254700000000"


def run():
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        ledger.get_or_create_vendor(db, DEMO_VENDOR_PHONE)
        ledger.log_purchase(db, DEMO_VENDOR_PHONE, "tilapia", quantity=15, cost=4500)
        ledger.log_purchase(db, DEMO_VENDOR_PHONE, "tomato", quantity=20, cost=500)
        print(f"Seeded demo vendor {DEMO_VENDOR_PHONE} with morning stock.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
