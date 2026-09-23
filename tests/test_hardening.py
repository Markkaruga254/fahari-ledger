"""
Regression tests for the hardening pass:

- Kenyan phone normalization (0711... == +254711... == 254711...)
- Ledger-layer validation (zero/negative/infinite amounts rejected)
- Customer-phone validation in the debt flow
- `today_summary` counts ALL outstanding debts, not just today's
- Cross-vendor invoice isolation over USSD
- Voice callbacks accept AT's real `callerNumber` field and never 422
- USSD callback works without `serviceCode`
"""
import asyncio
from datetime import timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.services import ledger
from app.ussd import menus
from app.ussd.session import clear_session


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


# --- phone normalization ----------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("+254700000010", "+254700000010"),
    ("  +254700000010  ", "+254700000010"),
    ("0700000010", "+254700000010"),
    ("254700000010", "+254700000010"),
    ("0711-111-111", "+254711111111"),
    ("+254 711 111 111", "+254711111111"),
    ("00254700000010", "+254700000010"),
])
def test_normalize_phone_kenyan_variants(raw, expected):
    assert ledger.normalize_phone(raw) == expected


@pytest.mark.parametrize("raw", ["+254711111111", "0711111111", "254711111111"])
def test_valid_phones_accepted(raw):
    assert ledger.is_valid_phone(raw) is True


@pytest.mark.parametrize("raw", ["", "abc", "123", "12", "+"])
def test_invalid_phones_rejected(raw):
    assert ledger.is_valid_phone(raw) is False


def test_phone_variants_resolve_to_same_vendor(db):
    vendor = ledger.get_or_create_vendor(db, "0700000020")
    same = ledger.get_or_create_vendor(db, "+254700000020")
    assert same.id == vendor.id
    assert same.phone_number == "+254700000020"


# --- ledger validation -------------------------------------------------------

@pytest.mark.parametrize("quantity,cost", [(0, 100), (-2, 100), (5, 0), (5, -1),
                                           (float("inf"), 100), (5, float("nan"))])
def test_log_purchase_rejects_bad_numbers(db, quantity, cost):
    with pytest.raises(ValueError, match="greater than 0"):
        ledger.log_purchase(db, "+254700000031", "tilapia", quantity, cost)


@pytest.mark.parametrize("quantity,price", [(0, 100), (5, 0), (-1, 100),
                                            (float("inf"), 100)])
def test_log_sale_rejects_bad_numbers(db, quantity, price):
    with pytest.raises(ValueError, match="greater than 0"):
        ledger.log_sale(db, "+254700000032", "tilapia", quantity, price)


def test_log_debt_rejects_bad_amount_and_phone(db):
    with pytest.raises(ValueError, match="greater than 0"):
        ledger.log_debt(db, "+254700000033", "+254711111111", "tilapia", -50)
    with pytest.raises(ValueError, match="invalid"):
        ledger.log_debt(db, "+254700000033", "not-a-number", "tilapia", 50)


def test_log_debt_normalizes_customer_phone(db):
    debt = ledger.log_debt(db, "+254700000034", "0711111111", "tilapia", 200)
    assert debt.customer_phone == "+254711111111"


def test_create_invoice_rejects_bad_amount(db):
    with pytest.raises(ValueError, match="greater than 0"):
        ledger.create_invoice(db, "+254700000035", "Nyali Hotel", 0)


def test_today_summary_includes_older_unsettled_debts(db):
    phone = "+254700000036"
    debt = ledger.log_debt(db, phone, "+254711111111", "tilapia", 1500)
    debt.created_at = debt.created_at - timedelta(days=3)
    db.commit()

    vendor = ledger.get_or_create_vendor(db, phone)
    summary = ledger.today_summary(db, vendor.id)

    assert summary["total_owed_to_vendor"] == 1500
    assert summary["debt_count"] == 1


# --- USSD flow hardening -----------------------------------------------------

USSD_PHONE = "+254700000099"


def _ussd_session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, autoflush=False, autocommit=False)


def setup_function():
    menus.notifications.send_sms = lambda *args, **kwargs: {"ok": True}
    engine, factory = _ussd_session_factory()
    menus.SessionLocal = factory
    setup_function.engine = engine
    for sid in ("hard-debt", "hard-inf", "hard-inv-a", "hard-inv-b", "hard-nosvc"):
        clear_session(sid)


def teardown_function():
    menus.SessionLocal = None
    setup_function.engine.dispose()


def _step(session_id, text, phone=USSD_PHONE):
    return menus.handle(session_id, phone, text)


def test_debt_flow_rejects_invalid_customer_phone_then_accepts_normalized():
    _step("hard-debt", "")
    _step("hard-debt", "3")
    response, ended = _step("hard-debt", "3*abc")
    assert ended is False
    assert "valid customer phone number" in response

    db = menus.SessionLocal()
    try:
        from app.db.models import Debt
        assert db.query(Debt).count() == 0  # invalid input persisted nothing
    finally:
        db.close()

    # Local 07... format is normalized to E.164 on commit.
    _step("hard-debt", "3*0711111111")
    _step("hard-debt", "3*0711111111*tilapia")
    _step("hard-debt", "3*0711111111*tilapia*500")
    response, ended = _step("hard-debt", "3*0711111111*tilapia*500*2")
    assert ended is True
    assert "+254711111111" in response

    db = menus.SessionLocal()
    try:
        from app.db.models import Debt
        assert db.query(Debt).one().customer_phone == "+254711111111"
    finally:
        db.close()


def test_purchase_flow_rejects_infinite_quantity():
    _step("hard-inf", "")
    _step("hard-inf", "1")
    _step("hard-inf", "1*tilapia")
    response, ended = _step("hard-inf", "1*tilapia*inf")
    assert ended is False
    assert "greater than 0" in response


def test_invoice_selection_is_scoped_to_calling_vendor():
    vendor_a = "+254700000101"
    vendor_b = "+254700000102"
    db = menus.SessionLocal()
    try:
        invoice_a = ledger.create_invoice(db, vendor_a, "Hotel A", 4200, 29)
        invoice_b = ledger.create_invoice(db, vendor_b, "Hotel B", 1000, 29)
        invoice_a_id, invoice_b_id = invoice_a.id, invoice_b.id
    finally:
        db.close()

    # Vendor B tries to act on vendor A's invoice: re-prompted, not committed.
    _step("hard-inv-b", "", phone=vendor_b)
    _step("hard-inv-b", "5", phone=vendor_b)
    response, ended = _step("hard-inv-b", f"5*{invoice_a_id}", phone=vendor_b)
    assert ended is False
    assert "valid invoice number" in response

    # Vendor B's own invoice still works end to end.
    response, ended = _step("hard-inv-b", f"5*{invoice_b_id}", phone=vendor_b)
    assert ended is False
    assert "Accept" in response
    response, ended = _step("hard-inv-b", f"5*{invoice_b_id}*2", phone=vendor_b)
    assert ended is True
    assert response == "END Invoice disputed."

    db = menus.SessionLocal()
    try:
        from app.db.models import Invoice
        status = {
            inv.id: inv.status.value for inv in db.query(Invoice).all()
        }
        assert status[invoice_a_id] == "pending"  # untouched by vendor B
        assert status[invoice_b_id] == "disputed"
    finally:
        db.close()


def test_ussd_callback_works_without_service_code():
    from app.ussd.router import ussd_callback

    response = asyncio.run(ussd_callback(
        sessionId="hard-nosvc",
        phoneNumber=USSD_PHONE,
        text="",
    ))
    assert response.startswith("CON Fahari Ledger")


# --- voice callback hardening -------------------------------------------------

def test_voice_recording_accepts_caller_number_field(monkeypatch):
    from app.db.models import Sale, Vendor
    from app.services import notifications
    from app.voice import router

    engine, factory = _ussd_session_factory()
    router.SessionLocal = factory
    try:
        monkeypatch.setattr(router, "transcribe", lambda url: "I sold 5kg tilapia for 3000")
        sent = []
        monkeypatch.setattr(
            notifications,
            "send_voice_sale_confirmation",
            lambda to, item, quantity, price: sent.append((to, item, quantity, price)),
        )

        # AT's real voice posts carry callerNumber, not phoneNumber.
        response = asyncio.run(router.voice_recording_callback(
            phoneNumber="",
            recordingUrl="https://example.test/recording.wav",
            callerNumber="+254700000103",
        ))
        body = response.body.decode("utf-8")
        assert response.media_type == "application/xml"
        assert "Confirmed: sold 5 tilapia" in body
        assert sent == [("+254700000103", "tilapia", 5.0, 3000.0)]

        db = router.SessionLocal()
        try:
            sale = db.query(Sale).one()
            vendor = db.query(Vendor).filter_by(phone_number="+254700000103").one()
            assert sale.vendor_id == vendor.id
            assert sale.source == "voice"
        finally:
            db.close()
    finally:
        router.SessionLocal = None
        engine.dispose()


def test_voice_recording_without_caller_falls_back_cleanly(monkeypatch):
    from app.voice import router

    monkeypatch.setattr(router, "transcribe", lambda url: (_ for _ in ()).throw(
        AssertionError("transcriber must not run without a caller")))
    response = asyncio.run(router.voice_recording_callback(
        phoneNumber="", recordingUrl="https://example.test/r.wav", callerNumber=""))
    assert "could not identify your number" in response.body.decode("utf-8")


def test_voice_recording_rejects_zero_quantity(monkeypatch):
    from app.db.models import Sale
    from app.voice import router

    engine, factory = _ussd_session_factory()
    router.SessionLocal = factory
    try:
        monkeypatch.setattr(router, "transcribe", lambda url: "0 kilo za tilapia bei 100")
        response = asyncio.run(router.voice_recording_callback(
            phoneNumber="+254700000104",
            recordingUrl="https://example.test/r.wav",
        ))
        assert "did not catch the full details" in response.body.decode("utf-8")

        db = router.SessionLocal()
        try:
            assert db.query(Sale).count() == 0  # nothing persisted
        finally:
            db.close()
    finally:
        router.SessionLocal = None
        engine.dispose()
