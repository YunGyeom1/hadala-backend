from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import date, datetime
from uuid import UUID

from . import models, schemas

def create_daily_settlement(
    db: Session,
    settlement: schemas.DailySettlementCreate
) -> models.DailySettlement:
    """일일 정산 정보를 생성합니다."""
    db_settlement = models.DailySettlement(**settlement.dict())
    db.add(db_settlement)
    db.commit()
    db.refresh(db_settlement)
    return db_settlement

def get_daily_settlement(
    db: Session,
    settlement_id: UUID
) -> Optional[models.DailySettlement]:
    """특정 일일 정산 정보를 조회합니다."""
    return db.query(models.DailySettlement)\
        .filter(models.DailySettlement.id == settlement_id)\
        .first()

def get_daily_settlements(
    db: Session,
    company_id: UUID,
    center_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.DailySettlement]:
    """일일 정산 정보 목록을 조회합니다."""
    query = db.query(models.DailySettlement)\
        .filter(models.DailySettlement.company_id == company_id)
    
    if center_id:
        query = query.filter(models.DailySettlement.center_id == center_id)
    if start_date:
        query = query.filter(models.DailySettlement.date >= start_date)
    if end_date:
        query = query.filter(models.DailySettlement.date <= end_date)
    
    return query.order_by(models.DailySettlement.date.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

def update_daily_settlement(
    db: Session,
    settlement_id: UUID,
    settlement_update: schemas.DailySettlementUpdate
) -> Optional[models.DailySettlement]:
    """일일 정산 정보를 업데이트합니다."""
    settlement = get_daily_settlement(db, settlement_id)
    if not settlement:
        return None
    
    update_data = settlement_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settlement, field, value)
    
    db.commit()
    db.refresh(settlement)
    return settlement

def create_daily_accounting(
    db: Session,
    accounting: schemas.DailyAccountingCreate
) -> models.DailyAccounting:
    """일일 회계 정보를 생성합니다."""
    db_accounting = models.DailyAccounting(**accounting.dict())
    db.add(db_accounting)
    db.commit()
    db.refresh(db_accounting)
    return db_accounting

def get_daily_accounting(
    db: Session,
    accounting_id: UUID
) -> Optional[models.DailyAccounting]:
    """특정 일일 회계 정보를 조회합니다."""
    return db.query(models.DailyAccounting)\
        .filter(models.DailyAccounting.id == accounting_id)\
        .first()

def get_daily_accountings(
    db: Session,
    company_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.DailyAccounting]:
    """일일 회계 정보 목록을 조회합니다."""
    query = db.query(models.DailyAccounting)\
        .filter(models.DailyAccounting.company_id == company_id)
    
    if start_date:
        query = query.filter(models.DailyAccounting.date >= start_date)
    if end_date:
        query = query.filter(models.DailyAccounting.date <= end_date)
    
    return query.order_by(models.DailyAccounting.date.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

def update_daily_accounting(
    db: Session,
    accounting_id: UUID,
    accounting_update: schemas.DailyAccountingUpdate
) -> Optional[models.DailyAccounting]:
    """일일 회계 정보를 업데이트합니다."""
    accounting = get_daily_accounting(db, accounting_id)
    if not accounting:
        return None
    
    update_data = accounting_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(accounting, field, value)
    
    db.commit()
    db.refresh(accounting)
    return accounting

def calculate_daily_settlement(
    db: Session,
    company_id: UUID,
    center_id: UUID,
    target_date: date
) -> Optional[models.DailySettlement]:
    """특정 일자의 정산 정보를 계산합니다."""
    # 도매 계약 입고 정보 집계
    wholesale_in = db.query(
        func.sum(models.WholesaleContractItem.quantity_kg).label('total_kg'),
        func.sum(models.WholesaleContractItem.total_price).label('total_price')
    ).join(
        models.WholesaleContract
    ).filter(
        and_(
            models.WholesaleContract.company_id == company_id,
            models.WholesaleContract.center_id == center_id,
            func.date(models.WholesaleContract.contract_date) == target_date
        )
    ).first()

    # 소매 계약 출고 정보 집계
    retail_out = db.query(
        func.sum(models.RetailContractItem.quantity_kg).label('total_kg'),
        func.sum(models.RetailContractItem.total_price).label('total_price')
    ).join(
        models.RetailContract
    ).filter(
        and_(
            models.RetailContract.company_id == company_id,
            models.RetailContract.center_id == center_id,
            func.date(models.RetailContract.contract_date) == target_date
        )
    ).first()

    # 정산 정보 생성
    settlement = models.DailySettlement(
        date=target_date,
        company_id=company_id,
        center_id=center_id,
        total_wholesale_in_kg=wholesale_in.total_kg or 0,
        total_wholesale_in_price=wholesale_in.total_price or 0,
        total_retail_out_kg=retail_out.total_kg or 0,
        total_retail_out_price=retail_out.total_price or 0
    )

    db.add(settlement)
    db.commit()
    db.refresh(settlement)
    return settlement

def calculate_daily_accounting(
    db: Session,
    company_id: UUID,
    target_date: date
) -> Optional[models.DailyAccounting]:
    """특정 일자의 회계 정보를 계산합니다."""
    # 도매 계약 결제 정보 집계
    wholesale_payments = db.query(
        func.sum(models.WholesaleContract.total_price).label('total_amount')
    ).filter(
        and_(
            models.WholesaleContract.company_id == company_id,
            func.date(models.WholesaleContract.contract_date) == target_date,
            models.WholesaleContract.payment_status == 'paid'
        )
    ).first()

    # 소매 계약 결제 정보 집계
    retail_payments = db.query(
        func.sum(models.RetailContract.total_price).label('total_amount')
    ).filter(
        and_(
            models.RetailContract.company_id == company_id,
            func.date(models.RetailContract.contract_date) == target_date,
            models.RetailContract.payment_status == 'paid'
        )
    ).first()

    # 회계 정보 생성
    accounting = models.DailyAccounting(
        date=target_date,
        company_id=company_id,
        total_paid=wholesale_payments.total_amount or 0,
        total_received=retail_payments.total_amount or 0
    )

    db.add(accounting)
    db.commit()
    db.refresh(accounting)
    return accounting 