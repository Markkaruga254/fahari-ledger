"""
Core business logic — deliberately isolated from telecom/external APIs.
This is the durable business-event layer underneath USSD, SMS and Voice.
"""
import math
import re
from datetime import datetime, timedelta

from app.utils.time import utc_now

from sqlalchemy.orm import Session

from app.db.models import Vendor, Purchase, Sale, Debt, Invoice, InvoiceStatus


def normalize_phone(phone_number: str) -> str:
    """Normalize a Kenyan phone number to E.164 (`+254...`).

    Africa's Talking always delivers the vendor's number as E.164, but the
    customer number in the debt flow is typed by the vendor on a feature
    phone, so `0711...`, `254711...`, `+254 711...` and `0711-111-111` must
    all resolve to the same record. Anything that doesn't look like a phone
    number is returned stripped (callers validate separately).
    """
    cleaned = re.sub(r"[\s\-()]", "", phone_number.strip())
    if cleaned.startswith("+"):
        return cleaned
    if cleaned.startswith("00"):
        return "+" + cleaned[2:]
    digits = re.sub(r"\D", "", cleaned)
    if digits.startswith("0") and len(digits) == 10:
        return "+254" + digits[1:]
    if digits.startswith("254") and len(digits) == 12:
        return "+" + digits
    return cleaned


def is_valid_phone(phone_number: str) -> bool:
    """Loose E.164 check: optional `+` followed by 9–15 digits."""
    return re.fullmatch(r"\+?\d{9,15}", normalize_phone(phone_number)) is not None


def _require_positive_finite(name: str, value: float) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be a number")
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be greater than 0")
    return value


def get_or_create_vendor(db: Session, phone_number: str) -> Vendor:
    phone_number = normalize_phone(phone_number)

    vendor = db.query(Vendor).filter(Vendor.phone_number == phone_number).first()
    if vendor is None:
        vendor = Vendor(phone_number=phone_number)
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
    return vendor


def log_purchase(db: Session, phone_number: str, item: str, quantity: float, cost: float, unit: str = "kg") -> Purchase:
    _require_positive_finite("quantity", quantity)
    _require_positive_finite("cost", cost)
    vendor = get_or_create_vendor(db, phone_number)
    purchase = Purchase(vendor_id=vendor.id, item=item, quantity=quantity, cost=cost, unit=unit)
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return purchase


def log_sale(
    db: Session,
    phone_number: str,
    item: str,
    quantity: float,
    price: float,
    unit: str = "kg",
    source: str = "ussd",
) -> Sale:
    _require_positive_finite("quantity", quantity)
    _require_positive_finite("price", price)
    vendor = get_or_create_vendor(db, phone_number)
    sale = Sale(
        vendor_id=vendor.id,
        item=item,
        quantity=quantity,
        price=price,
        unit=unit,
        source=source,
    )
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


def log_debt(
    db: Session,
    phone_number: str,
    customer_phone: str,
    item: str | None,
    amount: float,
    notify_customer: bool = False,
) -> Debt:
    _require_positive_finite("amount", amount)
    customer_phone = normalize_phone(customer_phone)
    if not is_valid_phone(customer_phone):
        raise ValueError("customer phone number is invalid")
    vendor = get_or_create_vendor(db, phone_number)
    debt = Debt(
        vendor_id=vendor.id,
        customer_phone=customer_phone,
        item=item,
        amount=amount,
        notify_customer=notify_customer,
    )
    db.add(debt)
    db.commit()
    db.refresh(debt)
    return debt


def stock_remaining(db: Session, vendor_id: int, item: str, since: datetime) -> float:
    purchased = sum(
        p.quantity
        for p in db.query(Purchase).filter(
            Purchase.vendor_id == vendor_id,
            Purchase.item == item,
            Purchase.created_at >= since,
        )
    )
    sold = sum(
        s.quantity
        for s in db.query(Sale).filter(
            Sale.vendor_id == vendor_id,
            Sale.item == item,
            Sale.created_at >= since,
        )
    )
    return max(purchased - sold, 0.0)


def today_summary(db: Session, vendor_id: int) -> dict:
    since = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)

    sales = db.query(Sale).filter(
        Sale.vendor_id == vendor_id,
        Sale.created_at >= since,
    ).all()
    purchases = db.query(Purchase).filter(
        Purchase.vendor_id == vendor_id,
        Purchase.created_at >= since,
    ).all()
    debts = db.query(Debt).filter(
        Debt.vendor_id == vendor_id,
        Debt.settled == False,  # noqa: E712
    ).all()

    total_sales = sum(s.price for s in sales)
    total_owed = sum(d.amount for d in debts)

    items_sold: dict[str, float] = {}
    items_purchased: dict[str, float] = {}
    for purchase in purchases:
        items_purchased[purchase.item] = items_purchased.get(purchase.item, 0) + purchase.quantity
    for sale in sales:
        items_sold[sale.item] = items_sold.get(sale.item, 0) + sale.quantity

    items_remaining = {
        item: max(items_purchased.get(item, 0) - items_sold.get(item, 0), 0.0)
        for item in items_purchased
    }

    return {
        "total_sales": total_sales,
        "total_owed_to_vendor": total_owed,
        "items_sold": items_sold,
        "items_purchased": items_purchased,
        "items_remaining": items_remaining,
        "sale_count": len(sales),
        "debt_count": len(debts),
    }


def create_invoice(
    db: Session,
    phone_number: str,
    buyer_name: str,
    amount: float,
    deadline_days: int = 30,
) -> Invoice:
    """Represents a simulated buyer-initiated (eTIMS) invoice event."""
    _require_positive_finite("amount", amount)
    vendor = get_or_create_vendor(db, phone_number)
    invoice = Invoice(
        vendor_id=vendor.id,
        buyer_name=buyer_name,
        amount=amount,
        status=InvoiceStatus.pending,
        deadline=utc_now() + timedelta(days=deadline_days),
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def respond_to_invoice(db: Session, invoice_id: int, accept: bool) -> Invoice:
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if invoice is None:
        raise ValueError("Invoice not found")
    if invoice.status != InvoiceStatus.pending:
        raise ValueError("Invoice is no longer pending")
    if utc_now() > invoice.deadline:
        invoice.status = InvoiceStatus.auto_rejected
        db.commit()
        raise ValueError("Invoice deadline has passed")
    invoice.status = InvoiceStatus.accepted if accept else InvoiceStatus.disputed
    db.commit()
    db.refresh(invoice)
    return invoice


def pending_invoices(db: Session, vendor_id: int):
    expired = db.query(Invoice).filter(
        Invoice.vendor_id == vendor_id,
        Invoice.status == InvoiceStatus.pending,
        Invoice.deadline < utc_now(),
    ).all()
    if expired:
        for invoice in expired:
            invoice.status = InvoiceStatus.auto_rejected
        db.commit()

    return db.query(Invoice).filter(
        Invoice.vendor_id == vendor_id,
        Invoice.status == InvoiceStatus.pending,
    ).all()
