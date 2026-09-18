"""
Simulates a buyer-initiated eTIMS invoice event. In production this would be
triggered by KRA's eTIMS system; here it's triggered manually (rehearsal) or
by a timer, so the demo's key differentiator doesn't depend on a real
integration that isn't feasible to build in the hackathon window.
"""
from app.db.session import SessionLocal
from app.services import ledger
from app.services import notifications


def fire_invoice_event(phone_number: str, buyer_name: str, amount: float, deadline_days: int = 30):
    db = SessionLocal()
    try:
        invoice = ledger.create_invoice(db, phone_number, buyer_name, amount, deadline_days)
        notifications.send_invoice_alert(phone_number, buyer_name, amount, deadline_days)
        return invoice
    finally:
        db.close()
