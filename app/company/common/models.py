from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Enum
import uuid
import enum

from app.database.base import Base

class CompanyType(enum.Enum):
    wholesaler = "wholesaler"
    retailer = "retailer"
    farmer = "farmer"

class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True, index=True)
    type = Column(Enum(CompanyType), nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    
    wholesale_company_detail_id = Column(UUID(as_uuid=True), ForeignKey("wholesale_company_details.company_id"), nullable=True)
    retail_company_detail_id = Column(UUID(as_uuid=True), ForeignKey("retail_company_details.company_id"), nullable=True)
    farm_company_detail_id = Column(UUID(as_uuid=True), ForeignKey("farmer_company_details.company_id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 관계 설정
    owner = relationship("Profile", back_populates="owned_companies")
    wholesaler_detail = relationship("WholesaleCompanyDetail", back_populates="company", uselist=False)
    retail_detail = relationship("RetailCompanyDetail", back_populates="company", uselist=False)
    farmer_detail = relationship("FarmerCompanyDetail", back_populates="company", uselist=False)
    
# class CompanyDetail(Base):
#     __tablename__ = "company_details"

#     company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), primary_key=True)
#     address = Column(String, nullable=True)
#     region = Column(String, nullable=True)
#     latitude = Column(Float, nullable=True)
#     longitude = Column(Float, nullable=True)
#     description = Column(String, nullable=True)
#     phone = Column(String, nullable=True)
#     email = Column(String, nullable=True)
#     representative = Column(String, nullable=True)
#     business_registration_number = Column(String, nullable=True)
#     established_year = Column(Integer, nullable=True)
    
#     created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

#     company = relationship("Company", back_populates="details")