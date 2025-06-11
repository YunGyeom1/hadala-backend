from datetime import datetime
import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, func, Date, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.transactions.common.models import ProductQuality

class CenterInvenrSnapshotItem(Base):
    __tablename__ = "center_snapshot_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    center_inventory_snapshot_id = Column(UUID(as_uuid=True, index=True), ForeignKey("center_inventory_snapshots.id"), nullable=False)
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    quality = Column(Enum(ProductQuality), nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    center_inventory = relationship("CenterInventory", back_populates="items")

class CenterInventorySnapshot(Base):
    __tablename__ = "center_inventory_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_date = Column(Date, nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True, index=True), ForeignKey("companies.id"), nullable=False)
    center_id = Column(UUID(as_uuid=True, index=True), ForeignKey("centers.id"), nullable=False)
    total_quantity = Column(Integer, nullable=False, default=0)
    total_price = Column(Float, nullable=False, default=0.0)
    finalized = Column(Boolean, nullable=False, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    center = relationship("Center", back_populates="snapshots")
    items = relationship("CenterSnapshotItem", back_populates="center_inventory")