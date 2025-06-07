from sqlalchemy import Column, String, Float, ForeignKey, Date, DateTime, Boolean
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from app.database.base import Base

class RetailShipment(Base):
    __tablename__ = "retail_shipments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    retailer_id = Column(String(36), ForeignKey("retailers.id"), nullable=False)
    contract_id = Column(String(36), ForeignKey("retail_contracts.id"), nullable=False)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    center_id = Column(String(36), ForeignKey("collection_centers.id"), nullable=False)
    wholesaler_id = Column(String(36), ForeignKey("wholesalers.id"), nullable=True)
    shipment_date = Column(Date, nullable=False)
    total_price = Column(Float, nullable=True)
    is_finalized = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    retailer = relationship("Retailer", back_populates="shipments")
    contract = relationship("RetailContract", back_populates="shipments")
    company = relationship("Company", back_populates="retail_shipments")
    center = relationship("CollectionCenter", back_populates="retail_shipments")
    wholesaler = relationship("Wholesaler", back_populates="retail_shipments")
    items = relationship("RetailShipmentItem", back_populates="shipment", cascade="all, delete-orphan")

class RetailShipmentItem(Base):
    __tablename__ = "retail_shipment_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    shipment_id = Column(String(36), ForeignKey("retail_shipments.id"), nullable=False)
    crop_name = Column(String(100), nullable=False)
    quantity_kg = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    quality_grade = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    shipment = relationship("RetailShipment", back_populates="items") 