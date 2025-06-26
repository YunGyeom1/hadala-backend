from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, date, timezone
from typing import Optional
from app.database.session import get_db
from app.profile.dependencies import get_current_profile
from app.profile.models import Profile
from app.company.common.crud import get_company_by_id
from . import crud, schemas

router = APIRouter(prefix="/payments", tags=["payments"])

@router.get("/report", response_model=schemas.PaymentReport)
def get_payment_report(
    start_date: Optional[date] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    현재 사용자의 회사 지급 현황 보고서를 반환합니다.
    날짜 범위를 지정하면 해당 기간의 계약만 포함됩니다.
    """
    if not current_profile.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="회사에 속해있지 않습니다"
        )
    
    return crud.get_payment_report(db, current_profile.company_id, start_date, end_date)

@router.get("/summary", response_model=schemas.PaymentSummary)
def get_payment_summary(
    start_date: Optional[date] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    현재 사용자의 회사 지급 현황 요약을 반환합니다.
    날짜 범위를 지정하면 해당 기간의 계약만 포함됩니다.
    """
    if not current_profile.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="회사에 속해있지 않습니다"
        )
    
    return crud.get_company_payment_summary(db, current_profile.company_id, start_date, end_date)

@router.get("/overdue")
def get_overdue_contracts(
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    현재 사용자의 회사 연체 계약 목록을 반환합니다.
    """
    if not current_profile.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="회사에 속해있지 않습니다"
        )
    
    overdue_contracts = crud.get_overdue_contracts(db, current_profile.company_id)
    return {
        "overdue_contracts": [
            {
                "id": str(contract.id),
                "title": contract.title,
                "total_price": contract.total_price,
                "payment_due_date": contract.payment_due_date.isoformat() if contract.payment_due_date else None,
                "days_overdue": abs((contract.payment_due_date - datetime.now(timezone.utc)).days) if contract.payment_due_date else 0
            }
            for contract in overdue_contracts
        ]
    } 