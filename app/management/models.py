from sqlalchemy import Column, String, Float, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID

from app.database.base import Base

class DailySettlement(Base):
    __tablename__ = "daily_settlements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    date = Column(Date, nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    center_id = Column(String(36), ForeignKey("collection_centers.id"), nullable=False)

    # 농가 입고 관련
    total_wholesale_in_kg = Column(Float, default=0)  # 농가 입고량 총합 (kg)
    total_wholesale_in_price = Column(Float, default=0)  # 농가 입고 금액 총합

    # 소매 출고 관련
    total_retail_out_kg = Column(Float, default=0)  # 소매 출고량 총합 (kg)
    total_retail_out_price = Column(Float, default=0)  # 소매 출고 금액 총합

    # 차이 관련
    discrepancy_in_kg = Column(Float)  # 입고 시 실제 vs 계약 차이 (kg)
    discrepancy_out_kg = Column(Float)  # 출고 시 실제 vs 계약 차이 (kg)

    # 총량 관련
    total_in_kg = Column(Float)  # 총 유입량 (입고 포함)
    total_out_kg = Column(Float)  # 총 유출량 (출고 포함)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    company = relationship("Company", back_populates="daily_settlements")
    center = relationship("CollectionCenter", back_populates="daily_settlements")

class DailyAccounting(Base):
    __tablename__ = "daily_accounting"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    date = Column(Date, nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)

    # 선지급/선수금 관련
    total_prepaid = Column(Float, default=0)  # 농가 선지급 금액 합계
    total_pre_received = Column(Float, default=0)  # 소매 선수금 수령 합계

    # 완료된 지급/수금 관련
    total_paid = Column(Float, default=0)  # 농가 지급 완료 금액
    total_received = Column(Float, default=0)  # 소매 수금 완료 금액

    # 미지급/미수금 관련
    total_pending_payment = Column(Float, default=0)  # 농가 미지급 잔액
    total_pending_receipt = Column(Float, default=0)  # 소매 미수금 잔액

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    company = relationship("Company", back_populates="daily_accounting") 