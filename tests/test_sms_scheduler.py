from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.services import ledger
from app.sms import scheduler


def test_overstock_alert_is_sent_once_per_vendor_item_day(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    scheduler.SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    scheduler.reset_overstock_alerts()

    sent = []
    monkeypatch.setattr(
        scheduler,
        "send_sms",
        lambda to, message: sent.append((to, message)),
    )
    monkeypatch.setattr(
        scheduler.overstock,
        "should_nudge",
        lambda purchased_qty, sold_qty: True,
    )

    db = scheduler.SessionLocal()
    try:
        vendor = ledger.get_or_create_vendor(db, "+254700000009")
        ledger.log_purchase(db, vendor.phone_number, "tilapia", 30, 12000)
        ledger.log_sale(db, vendor.phone_number, "tilapia", 5, 3000)
    finally:
        db.close()

    scheduler.check_overstock_job()
    scheduler.check_overstock_job()

    assert len(sent) == 1
    assert sent[0][0] == "+254700000009"
    assert "25.0kg tilapia" in sent[0][1]

    scheduler.reset_overstock_alerts()
    engine.dispose()
