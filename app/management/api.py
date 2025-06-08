from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from uuid import UUID

from app.database.session import get_db
from app.core.auth.utils import get_current_user
from app.user.models import User
from . import crud, schemas

router = APIRouter(prefix="/management", tags=["management"])

# 일일 정산 API
@router.post("/settlements/calculate", response_model=schemas.DailySettlement)
def calculate_settlement(
    center_id: UUID,
    target_date: date,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """특정 일자의 정산 정보를 계산합니다."""
    company_id = current_user.wholesaler.company_id
    settlement = crud.calculate_daily_settlement(db, company_id, center_id, target_date)
    if not settlement:
        raise HTTPException(status_code=404, detail="Failed to calculate settlement")
    return settlement

@router.get("/settlements", response_model=List[schemas.DailySettlement])
def get_settlements(
    center_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """일일 정산 정보 목록을 조회합니다."""
    company_id = current_user.wholesaler.company_id
    return crud.get_daily_settlements(
        db,
        company_id,
        center_id=center_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )

@router.get("/settlements/{settlement_id}", response_model=schemas.DailySettlement)
def get_settlement(
    settlement_id: UUID,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """특정 일일 정산 정보를 조회합니다."""
    company_id = current_user.wholesaler.company_id
    settlement = crud.get_daily_settlement(db, settlement_id)
    if not settlement or settlement.company_id != company_id:
        raise HTTPException(status_code=404, detail="Settlement not found")
    return settlement

@router.put("/settlements/{settlement_id}", response_model=schemas.DailySettlement)
def update_settlement(
    settlement_id: UUID,
    settlement_update: schemas.DailySettlementUpdate,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """일일 정산 정보를 업데이트합니다."""
    company_id = current_user.wholesaler.company_id
    settlement = crud.get_daily_settlement(db, settlement_id)
    if not settlement or settlement.company_id != company_id:
        raise HTTPException(status_code=404, detail="Settlement not found")
    
    updated_settlement = crud.update_daily_settlement(db, settlement_id, settlement_update)
    if not updated_settlement:
        raise HTTPException(status_code=404, detail="Failed to update settlement")
    return updated_settlement

# 일일 회계 API
@router.post("/accounting/calculate", response_model=schemas.DailyAccounting)
def calculate_accounting(
    target_date: date,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """특정 일자의 회계 정보를 계산합니다."""
    company_id = current_user.wholesaler.company_id
    accounting = crud.calculate_daily_accounting(db, company_id, target_date)
    if not accounting:
        raise HTTPException(status_code=404, detail="Failed to calculate accounting")
    return accounting

@router.get("/accounting", response_model=List[schemas.DailyAccounting])
def get_accountings(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """일일 회계 정보 목록을 조회합니다."""
    company_id = current_user.wholesaler.company_id
    return crud.get_daily_accountings(
        db,
        company_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )

@router.get("/accounting/{accounting_id}", response_model=schemas.DailyAccounting)
def get_accounting(
    accounting_id: UUID,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """특정 일일 회계 정보를 조회합니다."""
    company_id = current_user.wholesaler.company_id
    accounting = crud.get_daily_accounting(db, accounting_id)
    if not accounting or accounting.company_id != company_id:
        raise HTTPException(status_code=404, detail="Accounting not found")
    return accounting

@router.put("/accounting/{accounting_id}", response_model=schemas.DailyAccounting)
def update_accounting(
    accounting_id: UUID,
    accounting_update: schemas.DailyAccountingUpdate,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """일일 회계 정보를 업데이트합니다."""
    company_id = current_user.wholesaler.company_id
    accounting = crud.get_daily_accounting(db, accounting_id)
    if not accounting or accounting.company_id != company_id:
        raise HTTPException(status_code=404, detail="Accounting not found")
    
    updated_accounting = crud.update_daily_accounting(db, accounting_id, accounting_update)
    if not updated_accounting:
        raise HTTPException(status_code=404, detail="Failed to update accounting")
    return updated_accounting

@router.post("/settlements/today", response_model=schemas.DailySettlement)
def create_today_settlement(
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """오늘자 결산을 생성합니다."""
    settlement = crud.create_today_settlement(db, current_user.wholesaler.company_id)
    if not settlement:
        raise HTTPException(
            status_code=404,
            detail="최근 인벤토리 정보를 찾을 수 없습니다."
        )
    return settlement

@router.post("/settlements/today/center/{center_id}", response_model=schemas.DailySettlement)
def create_today_settlement_for_center(
    center_id: UUID,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """특정 센터의 오늘자 결산을 생성합니다."""
    settlement = crud.create_today_settlement(db, current_user.wholesaler.company_id, center_id)
    if not settlement:
        raise HTTPException(
            status_code=404,
            detail="최근 인벤토리 정보를 찾을 수 없습니다."
        )
    return settlement 