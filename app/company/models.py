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
    owner = Column(UUID(as_uuid=True), ForeignKey("wholesalers.id"), nullable=True)
    description = Column(String)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 관계
    centers = relationship("CollectionCenter", back_populates="company")
    wholesalers = relationship("Wholesaler", back_populates="company", foreign_keys="Wholesaler.company_id")