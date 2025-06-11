from datetime import date
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.company.shipment_summary.schemas import ShipmentSummary
from app.company.shipment_summary import crud
from app.profile.dependencies import get_current_profile
from app.profile.models import Profile

router = APIRouter()

@router.get("/date/{target_date}", response_model=ShipmentSummary)
def get_shipment_summary_by_date(
    target_date: date,
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile)
) -> ShipmentSummary:
    """
    특정 날짜의 출하 요약 정보를 조회합니다.
    """
    company_id = current_profile.company_id
    return crud.get_shipment_summary_by_date(db, target_date, company_id)

@router.get("/date-range", response_model=List[ShipmentSummary])
def get_shipment_summary_by_date_range(
    start_date: date = Query(..., description="시작 날짜"),
    end_date: date = Query(..., description="종료 날짜"),
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile)
) -> List[ShipmentSummary]:
    """
    특정 기간의 출하 요약 정보 목록을 조회합니다.
    """
    company_id = current_profile.company_id
    return crud.get_shipment_summary_by_date_range(db, start_date, end_date, company_id) 