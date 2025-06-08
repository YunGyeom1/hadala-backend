from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Date, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base
import uuid
import enum
from datetime import datetime

class ContractStatus(str, enum.Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class PaymentStatus(str, enum.Enum):
    PREPAID = "prepaid"
    PRE_RECEIVED = "pre-received"
    PAID = "paid"
    RECEIVED = "received"
    PENDING_PAYMENT = "pending_payment"
    PENDING_RECEIPT = "pending_receipt"
    PENDING = "pending"
    PARTIALLY_PAID = "partially_paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class WholesaleContract(Base):
    __tablename__ = "wholesale_contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    center_id = Column(UUID(as_uuid=True), ForeignKey("collection_centers.id"), nullable=False)
    wholesaler_id = Column(UUID(as_uuid=True), ForeignKey("wholesalers.id"), nullable=False)
    farmer_id = Column(UUID(as_uuid=True), ForeignKey("farmers.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    contract_date = Column(Date, nullable=False)
    contract_status = Column(Enum(ContractStatus), nullable=False, default=ContractStatus.DRAFT)
    note = Column(String)
    shipment_date = Column(Date, nullable=False)
    total_price = Column(Float)
    payment_status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    center = relationship("Center", back_populates="contracts")
    wholesaler = relationship("Wholesaler", back_populates="contracts")
    farmer = relationship("Farmer", back_populates="contracts")
    company = relationship("Company", back_populates="contracts")
    items = relationship("WholesaleContractItem", back_populates="contract", cascade="all, delete-orphan")
    shipments = relationship("WholesaleShipment", back_populates="contract")
    payment_logs = relationship("WholesaleContractPaymentLog", back_populates="contract")

class WholesaleContractItem(Base):
    __tablename__ = "wholesale_contract_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("wholesale_contracts.id"), nullable=False)
    crop_name = Column(String(100), nullable=False)
    quantity_kg = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    quality_required = Column(String(1), nullable=False)  # A, B, C
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    # Relationships
    contract = relationship("WholesaleContract", back_populates="items")

class WholesaleContractPaymentLog(Base):
    __tablename__ = "wholesale_contract_payment_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("wholesale_contracts.id"), nullable=False)
    old_status = Column(Enum(PaymentStatus), nullable=False)
    new_status = Column(Enum(PaymentStatus), nullable=False)
    changed_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    contract = relationship("WholesaleContract", back_populates="payment_logs")
    user = relationship("User") 