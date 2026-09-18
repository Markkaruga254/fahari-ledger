"""
Core business logic — deliberately isolated from telecom/external APIs.
This is the durable business-event layer underneath USSD, SMS and Voice.
"""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db.models import Vendor, Purchase, Sale, Debt, Invoice, InvoiceStatus


def get_or_create_vendor(db: Session, phone_number: str) -> Vendor:
    vendor = db.query(Vendor).filter(Vendor.phone_number == phone_number).first()
    if vendor is None:
        vendor = Vendor(phone_number=phone_number)
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
    return vendor


def log_purchase(db: Session, phone_number: str, item: str, quantity: float, cost: float, unit: str = "kg") -> Purchase:
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
    since = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

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
        Debt.created_at >= since,
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
    vendor = get_or_create_vendor(db, phone_number)
    invoice = Invoice(
        vendor_id=vendor.id,
        buyer_name=buyer_name,
        amount=amount,
        status=InvoiceStatus.pending,
        deadline=datetime.utcnow() + timedelta(days=deadline_days),
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
    if datetime.utcnow() > invoice.deadline:
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
        Invoice.deadline < datetime.utcnow(),
    ).all()
    if expired:
        for invoice in expired:
            invoice.status = InvoiceStatus.auto_rejected
        db.commit()

    return db.query(Invoice).filter(
        Invoice.vendor_id == vendor_id,
        Invoice.status == InvoiceStatus.pending,
    ).all()
