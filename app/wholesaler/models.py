from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base
import uuid

class Wholesaler(Base):
    __tablename__ = "wholesalers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    role = Column(String)
    name = Column(String, nullable=False)
    phone = Column(String)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 관계
    user = relationship("User", back_populates="wholesaler")
    company = relationship("Company", back_populates="wholesalers")
    collection_centers = relationship("CollectionCenterWholesaler", back_populates="wholesaler")