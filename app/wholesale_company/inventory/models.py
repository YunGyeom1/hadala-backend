from sqlalchemy import Column, String, Float, Date, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime

from app.database.base import Base

class CompanyCropInventory(Base):
    __tablename__ = "company_crop_inventory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    date = Column(Date, nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    center_id = Column(UUID(as_uuid=True), ForeignKey("collection_centers.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="inventories")
    center = relationship("Center", back_populates="inventories")
    items = relationship("CompanyCropInventoryItem", back_populates="inventory", cascade="all, delete-orphan")

class CompanyCropInventoryItem(Base):
    __tablename__ = "company_crop_inventory_item"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    inventory_id = Column(UUID(as_uuid=True), ForeignKey("company_crop_inventory.id"), nullable=False)
    crop_name = Column(String(100), nullable=False)
    quality_grade = Column(String(1), nullable=False)  # A, B, C
    quantity = Column(Float, nullable=False)  # kg 단위
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    inventory = relationship("CompanyCropInventory", back_populates="items") 

