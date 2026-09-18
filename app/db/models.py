from app.utils.time import utc_now

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
import enum

from app.db.session import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True)
    phone_number = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    purchases = relationship("Purchase", back_populates="vendor")
    sales = relationship("Sale", back_populates="vendor")
    debts = relationship("Debt", back_populates="vendor")
    invoices = relationship("Invoice", back_populates="vendor")


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    item = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, default="kg")
    cost = Column(Float, nullable=False)  # total cost, KES
    created_at = Column(DateTime, default=datetime.utcnow)

    vendor = relationship("Vendor", back_populates="purchases")


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    item = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, default="kg")
    price = Column(Float, nullable=False)  # total price, KES
    source = Column(String, default="ussd")  # ussd | voice
    created_at = Column(DateTime, default=datetime.utcnow)

    vendor = relationship("Vendor", back_populates="sales")


class Debt(Base):
    __tablename__ = "debts"

    id = Column(Integer, primary_key=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    customer_phone = Column(String, nullable=False)
    item = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    settled = Column(Boolean, default=False)
    notify_customer = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    vendor = relationship("Vendor", back_populates="debts")


class InvoiceStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    disputed = "disputed"
    auto_rejected = "auto_rejected"


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    buyer_name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.pending)
    deadline = Column(DateTime, nullable=False)  # 30 days from creation, per eTIMS buyer-initiated rule
    created_at = Column(DateTime, default=datetime.utcnow)

    vendor = relationship("Vendor", back_populates="invoices")
