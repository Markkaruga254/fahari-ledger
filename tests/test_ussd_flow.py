"""
USSD state-machine tests against an isolated SQLite database.

These tests exercise the same menu handler used by the FastAPI callback,
without requiring Africa's Talking or a live Postgres instance.
"""
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.ussd import menus
from app.ussd.session import clear_session
from app.db.models import Debt, Invoice, Purchase, Sale, Vendor


PHONE = "+254700000009"


def setup_function():
    menus.send_sms = lambda *args, **kwargs: {"ok": True}
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    menus.SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    setup_function.db = engine
    clear_session("ussd-test")
    clear_session("ussd-sale")
    clear_session("ussd-debt")
    clear_session("ussd-invoice")


def teardown_function():
    menus.SessionLocal = None
    setup_function.db.dispose()


def step(session_id, text):
    return menus.handle(session_id, PHONE, text)


def test_sale_flow_persists_sale():
    step("ussd-sale", "")
    assert step("ussd-sale", "2")[0].startswith("CON")
    assert step("ussd-sale", "2*tilapia")[0].startswith("CON")
    assert step("ussd-sale", "2*tilapia*3")[0].startswith("CON")
    response, ended = step("ussd-sale", "2*tilapia*3*900")

    assert ended is True
    assert response == "END Logged: sold 3kg tilapia for KES 900."

    db = menus.SessionLocal()
    try:
        vendor = db.query(Vendor).filter_by(phone_number=PHONE).one()
        sale = db.query(Sale).filter_by(vendor_id=vendor.id).one()
        assert sale.item == "tilapia"
        assert sale.quantity == 3
        assert sale.price == 900
    finally:
        db.close()


def test_purchase_flow_rejects_invalid_numbers_then_commits():
    step("ussd-test", "")
    step("ussd-test", "1")
    assert step("ussd-test", "1*tilapia")[0].startswith("CON")

    response, ended = step("ussd-test", "1*tilapia*-2")
    assert ended is False
    assert "greater than 0" in response

    step("ussd-test", "1*tilapia*10")
    response, ended = step("ussd-test", "1*tilapia*10*12000")
    assert ended is True
    assert "bought 10kg tilapia" in response

    db = menus.SessionLocal()
    try:
        assert db.query(Purchase).count() == 1
        assert db.query(Purchase).one().cost == 12000
    finally:
        db.close()


def test_debt_flow_records_and_requires_notification_choice():
    step("ussd-debt", "")
    step("ussd-debt", "3")
    step("ussd-debt", "3*+254711111111")
    step("ussd-debt", "3*+254711111111*tilapia")
    step("ussd-debt", "3*+254711111111*tilapia*2000")

    response, ended = step("ussd-debt", "3*+254711111111*tilapia*2000*3")
    assert ended is False
    assert "Choose 1 for Yes or 2 for No" in response

    sent = []
    menus.send_sms = lambda to, message: sent.append((to, message))

    response, ended = step("ussd-debt", "3*+254711111111*tilapia*2000*1")
    assert ended is True
    assert "KES 2000 owed" in response
    assert sent == [(
        "+254711111111",
        "You owe the seller KES 2000 for tilapia, logged today via Fahari Ledger.",
    )]

    db = menus.SessionLocal()
    try:
        debt = db.query(Debt).one()
        assert debt.customer_phone == "+254711111111"
        assert debt.amount == 2000
        assert debt.notify_customer is True
    finally:
        db.close()


def test_invoice_flow_accepts_pending_invoice():
    from app.services import ledger

    db = menus.SessionLocal()
    invoice = ledger.create_invoice(db, PHONE, "Nyali Hotel Supplies", 4200, 29)
    invoice_id = invoice.id
    db.close()

    step("ussd-invoice", "")
    response, ended = step("ussd-invoice", "5")
    assert ended is False
    assert "Nyali Hotel Supplies" in response

    response, ended = step("ussd-invoice", f"5*{invoice_id}")
    assert ended is False
    assert "Accept" in response

    response, ended = step("ussd-invoice", f"5*{invoice_id}*1")
    assert ended is True
    assert response == "END Invoice accepted."

    db = menus.SessionLocal()
    try:
        assert db.query(Invoice).one().status.value == "accepted"
    finally:
        db.close()


def test_check_today_uses_phone_from_handler():
    from app.services import ledger

    db = menus.SessionLocal()
    ledger.log_purchase(db, PHONE, "tilapia", 30, 12000)
    ledger.log_sale(db, PHONE, "tilapia", 13, 7800)
    ledger.log_debt(db, PHONE, "+254711111111", "tilapia", 2000)
    db.close()

    response, ended = step("ussd-check", "4")
    assert ended is True
    assert "KES 7800 sold" in response
    assert "KES 2000 owed" in response
    assert "stock tilapia: 17kg" in response
