from datetime import datetime
import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Enum, func, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.transactions.common.models import ShipmentStatus, ProductQuality

class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    title = Column(String, nullable=False)
    notes = Column(String)
    
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id"), nullable=False, index=True)
    
    creator_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False, index=True)
    supplier_person_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), index=True)
    supplier_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    receiver_person_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), index=True)
    receiver_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    departure_center_id = Column(UUID(as_uuid=True), ForeignKey("centers.id"), index=True)
    arrival_center_id = Column(UUID(as_uuid=True), ForeignKey("centers.id"), index=True)
    
    shipment_datetime = Column(DateTime(timezone=True))
    shipment_status = Column(Enum(ShipmentStatus), nullable=False, default=ShipmentStatus.PENDING)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    contract = relationship("Contract")
    creator = relationship("Profile", foreign_keys=[creator_id])
    supplier_person = relationship("Profile", foreign_keys=[supplier_person_id])
    supplier_company = relationship("Company", foreign_keys=[supplier_company_id])
    receiver_person = relationship("Profile", foreign_keys=[receiver_person_id])
    receiver_company = relationship("Company", foreign_keys=[receiver_company_id])
    departure_center = relationship("Center", foreign_keys=[departure_center_id])
    arrival_center = relationship("Center", foreign_keys=[arrival_center_id])
    items = relationship("ShipmentItem", back_populates="shipment", cascade="all, delete-orphan")

class ShipmentItem(Base):
    __tablename__ = "shipment_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.id"), nullable=False, index=True)
    
    product_name = Column(String, nullable=False)
    quality = Column(Enum(ProductQuality), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    shipment = relationship("Shipment", back_populates="items")
    