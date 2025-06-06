from sqlalchemy import Column, String, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base
import uuid

class CollectionCenter(Base):
    __tablename__ = "collection_centers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    name = Column(String, nullable=False)
    address = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    company = relationship("Company", back_populates="centers")
    wholesalers = relationship("CollectionCenterWholesaler", back_populates="center")

class CollectionCenterWholesaler(Base):
    __tablename__ = "collection_center_wholesaler"

    collection_center_id = Column(UUID(as_uuid=True), ForeignKey("collection_centers.id"), primary_key=True)
    wholesaler_id = Column(UUID(as_uuid=True), ForeignKey("wholesalers.id"), primary_key=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 관계
    center = relationship("CollectionCenter", back_populates="wholesalers")
    wholesaler = relationship("Wholesaler", back_populates="collection_centers")