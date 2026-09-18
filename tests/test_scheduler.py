from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.services import ledger
from app.sms import scheduler


def test_eod_summary_sent_for_purchase_only_vendor(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    scheduler.SessionLocal = sessionmaker(bind=engine)

    db = scheduler.SessionLocal()
    ledger.log_purchase(db, "+254700000010", "tilapia", 30, 12000)
    db.close()

    sent = []
    monkeypatch.setattr(scheduler, "send_sms", lambda phone, message: sent.append((phone, message)))

    scheduler.send_eod_summaries_job()

    assert len(sent) == 1
    assert sent[0][0] == "+254700000010"
    assert "Stock remaining: tilapia 30kg." in sent[0][1]
