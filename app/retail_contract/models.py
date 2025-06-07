from sqlalchemy import Column, String, Float, Date, ForeignKey, DateTime, Enum
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

class RetailContract(Base):
    __tablename__ = "retail_contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    retailer_id = Column(UUID(as_uuid=True), ForeignKey("retailers.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    center_id = Column(UUID(as_uuid=True), ForeignKey("collection_centers.id"), nullable=False)
    wholesaler_id = Column(UUID(as_uuid=True), ForeignKey("wholesalers.id"), nullable=False)
    contract_date = Column(DateTime, nullable=False)
    contract_status = Column(Enum(ContractStatus), nullable=False, default=ContractStatus.DRAFT)
    note = Column(String(500))
    shipment_date = Column(Date, nullable=False)
    total_price = Column(Float)
    payment_status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    retailer = relationship("Retailer", back_populates="retail_contracts")
    company = relationship("Company", back_populates="retail_contracts")
    center = relationship("Center", back_populates="retail_contracts")
    wholesaler = relationship("Wholesaler", back_populates="retail_contracts")
    items = relationship("RetailContractItem", back_populates="contract", cascade="all, delete-orphan")
    shipments = relationship("RetailShipment", back_populates="contract")
    payment_logs = relationship("RetailContractPaymentLog", back_populates="contract")

class RetailContractItem(Base):
    __tablename__ = "retail_contract_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String(36), ForeignKey("retail_contracts.id"), nullable=False)
    crop_name = Column(String(100), nullable=False)
    quantity_kg = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    quality_required = Column(String(1), nullable=False)  # A, B, C
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    contract = relationship("RetailContract", back_populates="items")

class RetailContractPaymentLog(Base):
    __tablename__ = "retail_contract_payment_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("retail_contracts.id"), nullable=False)
    old_status = Column(Enum(PaymentStatus), nullable=False)
    new_status = Column(Enum(PaymentStatus), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    contract = relationship("RetailContract", back_populates="payment_logs")
    user = relationship("User") 