from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database.base import Base
from sqlalchemy.types import DateTime
from sqlalchemy.orm import relationship

class FarmerCompanyDetail(Base):
    __tablename__ = "farmer_company_details"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", use_alter=True), primary_key=True)

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

    # 농가 전용 필드
    main_products = Column(String, nullable=True)               # 주요 상품 (CSV 형식)
    farm_size = Column(Float, nullable=True)                    # 농장 사이즈 (평방미터)
    annual_production = Column(Float, nullable=True)            # 연 생산량
    cultivation_method = Column(String, nullable=True)          # 재배 방식
    certification_info = Column(String, nullable=True)          # 인증 정보 (친환경 등, CSV 형식)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    company = relationship(
        "Company",
        foreign_keys=[company_id]
    ) 
    