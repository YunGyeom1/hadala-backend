from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base
import uuid

class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    owner = Column(
    UUID(as_uuid=True),
    ForeignKey("wholesalers.id", use_alter=True, name="fk_companies_wholesalers_owner"),
    nullable=True)
    description = Column(String)
    business_number = Column(String(50), unique=True, nullable=False)
    address = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(100), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 관계
    centers = relationship("Center", back_populates="company")
    wholesalers = relationship("Wholesaler", back_populates="company", foreign_keys="Wholesaler.company_id")
    contracts = relationship("WholesaleContract", back_populates="company")
    shipments = relationship("WholesaleShipment", back_populates="company")
    retail_contracts = relationship("RetailContract", back_populates="company")
    retail_shipments = relationship("RetailShipment", back_populates="company")
    inventories = relationship("CompanyCropInventory", back_populates="company")
    daily_settlements = relationship("DailySettlement", back_populates="company")
    daily_accounting = relationship("DailyAccounting", back_populates="company")