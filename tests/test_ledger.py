from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.services import ledger


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_log_sale_and_summary_includes_remaining_stock(db):
    phone = "+254700000001"
    ledger.log_purchase(db, phone, "tomato", 10, 250)
    ledger.log_sale(db, phone, "tomato", 3, 90)

    vendor = ledger.get_or_create_vendor(db, phone)
    summary = ledger.today_summary(db, vendor.id)

    assert summary["total_sales"] == 90
    assert summary["sale_count"] == 1
    assert summary["items_sold"]["tomato"] == 3
    assert summary["items_purchased"]["tomato"] == 10
    assert summary["items_remaining"]["tomato"] == 7


def test_log_debt_tracked_as_owed(db):
    phone = "+254700000002"
    ledger.log_debt(db, phone, "+254711111111", "sukuma", 200)

    vendor = ledger.get_or_create_vendor(db, phone)
    summary = ledger.today_summary(db, vendor.id)

    assert summary["total_owed_to_vendor"] == 200
    assert summary["debt_count"] == 1


def test_invoice_lifecycle(db):
    phone = "+254700000003"
    invoice = ledger.create_invoice(db, phone, "Nyali Hotel", 4200, deadline_days=29)
    assert invoice.status.value == "pending"

    updated = ledger.respond_to_invoice(db, invoice.id, accept=True)
    assert updated.status.value == "accepted"


def test_expired_invoice_cannot_be_accepted(db):
    phone = "+254700000004"
    invoice = ledger.create_invoice(db, phone, "Nyali Hotel", 4200, deadline_days=-1)

    with pytest.raises(ValueError, match="deadline"):
        ledger.respond_to_invoice(db, invoice.id, accept=True)

    assert invoice.status.value == "auto_rejected"


def test_stock_never_goes_negative(db):
    phone = "+254700000005"
    ledger.log_purchase(db, phone, "tilapia", 5, 1500)
    ledger.log_sale(db, phone, "tilapia", 7, 2100)

    vendor = ledger.get_or_create_vendor(db, phone)
    assert ledger.stock_remaining(
        db,
        vendor.id,
        "tilapia",
        datetime.utcnow() - timedelta(days=1),
    ) == 0
