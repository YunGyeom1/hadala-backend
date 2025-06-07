from sqlalchemy import Column, String, Float, Date, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base
import uuid
import enum

class ContractStatus(str, enum.Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PaymentStatus(str, enum.Enum):
    PREPAID = "prepaid"
    PRE_RECEIVED = "pre-received"
    PAID = "paid"
    RECEIVED = "received"
    PENDING_PAYMENT = "pending_payment"
    PENDING_RECEIPT = "pending_receipt"

class RetailContract(Base):
    __tablename__ = "retail_contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    retailer_id = Column(UUID(as_uuid=True), ForeignKey("retailers.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    center_id = Column(UUID(as_uuid=True), ForeignKey("collection_centers.id"), nullable=False)
    wholesaler_id = Column(UUID(as_uuid=True), ForeignKey("wholesalers.id"), nullable=False)
    contract_date = Column(Date, nullable=False)
    contract_status = Column(Enum(ContractStatus), nullable=False, default=ContractStatus.DRAFT)
    note = Column(String)
    shipment_date = Column(Date, nullable=False)
    total_price = Column(Float)
    payment_status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING_PAYMENT)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 관계
    retailer = relationship("Retailer", back_populates="retail_contracts")
    company = relationship("Company", back_populates="retail_contracts")
    center = relationship("CollectionCenter", back_populates="retail_contracts")
    wholesaler = relationship("Wholesaler", back_populates="retail_contracts")
    items = relationship("RetailContractItem", back_populates="contract", cascade="all, delete-orphan")

class RetailContractItem(Base):
    __tablename__ = "retail_contract_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("retail_contracts.id"), nullable=False)
    crop_name = Column(String, nullable=False)
    min_quantity_kg = Column(Float)
    max_quantity_kg = Column(Float)
    unit_price = Column(Float, nullable=False)
    quality_required = Column(String)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 관계
    contract = relationship("RetailContract", back_populates="items") 