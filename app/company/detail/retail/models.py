from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database.base import Base
from sqlalchemy.types import DateTime
from sqlalchemy.orm import relationship

class RetailCompanyDetail(Base):
    __tablename__ = "retail_company_details"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), primary_key=True)

    # 공통 필드
    address = Column(String, nullable=True)
    region = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    description = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    representative = Column(String, nullable=True)
    business_registration_number = Column(String, nullable=True)
    established_year = Column(Integer, nullable=True)

    # 소매회사 전용 필드
    daily_consumption = Column(Float, nullable=True)            # 일 소비량
    main_products = Column(String, nullable=True)               # 주요 상품 (CSV 형식)
    preferred_delivery_day = Column(String, nullable=True)      # 선호 납품일

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    company = relationship("Company", back_populates="retail_detail") 