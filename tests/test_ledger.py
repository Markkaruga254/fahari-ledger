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


def test_log_sale_and_summary(db):
    phone = "+254700000001"
    ledger.log_purchase(db, phone, "tomato", 10, 250)
    ledger.log_sale(db, phone, "tomato", 3, 90)

    vendor = ledger.get_or_create_vendor(db, phone)
    summary = ledger.today_summary(db, vendor.id)

    assert summary["total_sales"] == 90
    assert summary["sale_count"] == 1
    assert summary["items_sold"]["tomato"] == 3


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
