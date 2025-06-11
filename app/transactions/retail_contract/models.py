from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Enum, JSON, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base
import uuid
from app.transactions.common.models import ContractStatus, PaymentStatus, ProductQuality


class RetailContractItem(Base):
    __tablename__ = "retail_contract_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("retail_contracts.id"), nullable=False)
    product_name = Column(String, nullable=False)  # 작물명
    quality = Column(Enum(ProductQuality), nullable=False)  # 퀄리티
    quantity = Column(Float, nullable=False)  # 양
    unit_price = Column(Float, nullable=False)  # 단위가격
    total_price = Column(Float, nullable=False)  # 총 가격

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    contract = relationship("RetailContract", back_populates="items")

    # Indexes
    __table_args__ = (
        Index('ix_retail_contract_items_contract_id', 'contract_id'),
    )

class RetailContract(Base):
    __tablename__ = "retail_contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    supplier_contractor_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    supplier_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    receiver_contractor_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    receiver_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    delivery_datetime = Column(DateTime(timezone=True))
    delivery_location = Column(String)
    total_price = Column(Float, nullable=False)
    payment_due_date = Column(DateTime(timezone=True))
    contract_status = Column(Enum(ContractStatus), nullable=False, default=ContractStatus.DRAFT)
    payment_status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    notes = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    supplier_contractor = relationship("Profile", foreign_keys=[supplier_contractor_id])
    supplier_company = relationship("Company", foreign_keys=[supplier_company_id])
    receiver_contractor = relationship("Profile", foreign_keys=[receiver_contractor_id])
    receiver_company = relationship("Company", foreign_keys=[receiver_company_id])
    next_contract = relationship("RetailContract", remote_side=[id], backref="previous_contract")
    items = relationship("RetailContractItem", back_populates="contract", cascade="all, delete-orphan")
    creator = relationship("Profile", foreign_keys=[creator_id])

    # Indexes
    __table_args__ = (
        Index('ix_retail_contracts_creator_id', 'creator_id'),
        Index('ix_retail_contracts_supplier_contractor_id', 'supplier_contractor_id'),
        Index('ix_retail_contracts_supplier_company_id', 'supplier_company_id'),
        Index('ix_retail_contracts_receiver_contractor_id', 'receiver_contractor_id'),
        Index('ix_retail_contracts_receiver_company_id', 'receiver_company_id'),
    ) 