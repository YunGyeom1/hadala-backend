from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    email = Column(String, unique=True, index=True, nullable=False)
    picture_url = Column(String)
    oauth_provider = Column(String, nullable=False)   # 예: "google"
    oauth_sub = Column(String, nullable=False, index=True)  # 구글 'sub'

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 관계
    # farmer = relationship("Farmer", back_populates="user", uselist=False)
    # wholesaler = relationship("Wholesaler", back_populates="user", uselist=False)