from sqlalchemy import Column, String, DateTime, ForeignKey, UUID, func, Table
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from app.database.base import Base

# Association table for many-to-many relationship between centers and wholesalers
center_wholesaler = Table(
    "center_wholesaler",
    Base.metadata,
    Column("center_id", String(36), ForeignKey("collection_centers.id"), primary_key=True),
    Column("wholesaler_id", String(36), ForeignKey("wholesalers.id"), primary_key=True)
)

class CollectionCenter(Base):
    __tablename__ = "collection_centers"

    id = Column(UUID, primary_key=True, index=True)
    company_id = Column(UUID, ForeignKey("companies.id"), nullable=False)
    name = Column(String, nullable=False)
    address = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="centers")
    wholesalers = relationship("Wholesaler", secondary=center_wholesaler, back_populates="centers")
    contracts = relationship("WholesaleContract", back_populates="center")
    shipments = relationship("WholesaleShipment", back_populates="center")
    retail_contracts = relationship("RetailContract", back_populates="center")
    retail_shipments = relationship("RetailShipment", back_populates="center")
    inventories = relationship("CompanyCropInventory", back_populates="center")
    daily_settlements = relationship("DailySettlement", back_populates="center")

class CollectionCenterWholesaler(Base):
    __tablename__ = "collection_center_wholesaler"
    collection_center_id = Column(UUID, ForeignKey("collection_centers.id"), primary_key=True)
    wholesaler_id = Column(UUID, ForeignKey("wholesalers.id"), primary_key=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())