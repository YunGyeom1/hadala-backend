from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    picture_url = Column(String)
    oauth_provider = Column(String, nullable=True)  # Google, Kakao 등
    oauth_sub = Column(String, nullable=False, index=True)  # Google OAuth sub

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 관계
    farmer = relationship("Farmer", back_populates="user", uselist=False)
    wholesaler = relationship("Wholesaler", back_populates="user", uselist=False)
    retailer = relationship("Retailer", back_populates="user", uselist=False)