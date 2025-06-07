from sqlalchemy import Column, String, Float, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime

from app.database.base import Base

class CompanyCropInventory(Base):
    __tablename__ = "company_crop_inventory"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    date = Column(Date, nullable=False)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    center_id = Column(String(36), ForeignKey("centers.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="inventories")
    center = relationship("CollectionCenter", back_populates="inventories")
    items = relationship("CompanyCropInventoryItem", back_populates="inventory", cascade="all, delete-orphan")

class CompanyCropInventoryItem(Base):
    __tablename__ = "company_crop_inventory_item"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    inventory_id = Column(String(36), ForeignKey("company_crop_inventory.id"), nullable=False)
    crop_name = Column(String(100), nullable=False)
    quality_grade = Column(String(1), nullable=False)  # A, B, C
    quantity = Column(Float, nullable=False)  # kg 단위
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    inventory = relationship("CompanyCropInventory", back_populates="items") 