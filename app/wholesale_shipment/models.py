from sqlalchemy import Column, String, Float, Date, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base
import uuid

class WholesaleShipment(Base):
    __tablename__ = "wholesale_shipments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("wholesale_contracts.id"), nullable=False)
    farmer_id = Column(UUID(as_uuid=True), ForeignKey("farmers.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    center_id = Column(UUID(as_uuid=True), ForeignKey("collection_centers.id"), nullable=False)
    wholesaler_id = Column(UUID(as_uuid=True), ForeignKey("wholesalers.id"), nullable=False)
    shipment_date = Column(Date, nullable=False)
    total_price = Column(Float)
    is_finalized = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 관계
    contract = relationship("WholesaleContract", back_populates="shipments")
    farmer = relationship("Farmer", back_populates="shipments")
    company = relationship("Company", back_populates="shipments")
    center = relationship("Center", back_populates="shipments")
    wholesaler = relationship("Wholesaler", back_populates="shipments")
    items = relationship("WholesaleShipmentItem", back_populates="shipment", cascade="all, delete-orphan")

class WholesaleShipmentItem(Base):
    __tablename__ = "wholesale_shipment_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("wholesale_shipments.id"), nullable=False)
    crop_name = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    quality_grade = Column(String)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 관계
    shipment = relationship("WholesaleShipment", back_populates="items") 