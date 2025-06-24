from sqlalchemy import Column, String, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base
import uuid
import enum
from typing import Optional

class ProfileType(enum.Enum):
    wholesaler = "wholesaler"
    retailer = "retailer"
    farmer = "farmer"

class ProfileRole(enum.Enum):
    owner = "owner"
    manager = "manager"
    member = "member"

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    type = Column(Enum(ProfileType), nullable=False)
    username = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    phone = Column(String)
    email = Column(String)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    role = Column(Enum(ProfileRole), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="profiles")
    company = relationship("Company", foreign_keys=[company_id])
    owned_companies = relationship("Company", foreign_keys="Company.owner_id", back_populates="owner")

    @property
    def company_name(self) -> Optional[str]:
        """회사명을 반환합니다."""
        return self.company.name if self.company else None