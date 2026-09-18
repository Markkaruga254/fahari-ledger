"""
End-to-end test for the simulated buyer invoice -> SMS -> USSD response loop.
"""
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.db.models import Invoice, Vendor
from app.etims_sim import event_generator
from app.services import notifications
from app.ussd import menus
from app.ussd.session import clear_session


PHONE = "+254700000010"


def setup_function():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    event_generator.SessionLocal = session_factory
    menus.SessionLocal = session_factory
    setup_function.db = engine

    clear_session("etims-flow")
    setup_function.sent = []


def teardown_function():
    event_generator.SessionLocal = None
    menus.SessionLocal = None
    setup_function.db.dispose()


def test_invoice_event_reaches_vendor_and_can_be_accepted_via_ussd(monkeypatch):
    def fake_invoice_alert(to, buyer_name, amount, days_left):
        setup_function.sent.append((to, buyer_name, amount, days_left))
        return {"ok": True}

    monkeypatch.setattr(notifications, "send_invoice_alert", fake_invoice_alert)

    invoice = event_generator.fire_invoice_event(
        PHONE,
        "Nyali Hotel Supplies",
        4200,
        deadline_days=29,
    )

    assert invoice.status.value == "pending"
    assert setup_function.sent == [
        (PHONE, "Nyali Hotel Supplies", 4200, 29),
    ]

    db = menus.SessionLocal()
    try:
        persisted = db.query(Invoice).one()
        vendor = db.query(Vendor).filter_by(phone_number=PHONE).one()
        assert persisted.vendor_id == vendor.id
        assert persisted.buyer_name == "Nyali Hotel Supplies"
        assert persisted.amount == 4200
    finally:
        db.close()

    assert menus.handle("etims-flow", PHONE, "")[0].startswith("CON")
    response, ended = menus.handle("etims-flow", PHONE, "5")
    assert ended is False
    assert "Nyali Hotel Supplies" in response
    assert "29d left" in response

    response, ended = menus.handle(
        "etims-flow",
        PHONE,
        f"5*{invoice.id}",
    )
    assert ended is False
    assert "Accept" in response

    response, ended = menus.handle(
        "etims-flow",
        PHONE,
        f"5*{invoice.id}*1",
    )
    assert ended is True
    assert response == "END Invoice accepted."

    db = menus.SessionLocal()
    try:
        assert db.query(Invoice).one().status.value == "accepted"
    finally:
        db.close()
