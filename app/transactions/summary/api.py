from datetime import date
from typing import List
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.transactions.summary.schemas import SummaryRequest, SummaryResponse, TransactionType, Direction
from app.transactions.summary import services
from app.profile.dependencies import get_current_profile
from app.profile.models import Profile

router = APIRouter(prefix="/summary", tags=["summary"])

@router.post("/daily-summary", response_model=SummaryResponse)
def get_daily_summary_by_request(
    request: SummaryRequest,
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile)
) -> SummaryResponse:
    """
    SummaryRequest를 기반으로 일자별 종합 데이터를 반환합니다.
    """
    # 현재 사용자의 회사 ID로 요청 업데이트
    request.company_id = current_profile.company_id
    
    return services.get_daily_summary_by_request(db, request)

@router.get("/contracts/outbound", response_model=SummaryResponse)
def get_contract_outbound_summary(
    start_date: date = Query(..., description="시작 날짜"),
    end_date: date = Query(..., description="종료 날짜"),
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile)
) -> SummaryResponse:
    """
    회사의 출고 계약 요약을 조회합니다.
    """
    request = SummaryRequest(
        start_date=start_date,
        end_date=end_date,
        direction=Direction.OUTBOUND,
        transaction_type=TransactionType.CONTRACT,
        company_id=current_profile.company_id
    )
    
    return services.get_daily_summary_by_request(db, request)

@router.get("/contracts/inbound", response_model=SummaryResponse)
def get_contract_inbound_summary(
    start_date: date = Query(..., description="시작 날짜"),
    end_date: date = Query(..., description="종료 날짜"),
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile)
) -> SummaryResponse:
    """
    회사의 입고 계약 요약을 조회합니다.
    """
    request = SummaryRequest(
        start_date=start_date,
        end_date=end_date,
        direction=Direction.INBOUND,
        transaction_type=TransactionType.CONTRACT,
        company_id=current_profile.company_id
    )
    
    return services.get_daily_summary_by_request(db, request)

@router.get("/shipments/outbound", response_model=SummaryResponse)
def get_shipment_outbound_summary(
    start_date: date = Query(..., description="시작 날짜"),
    end_date: date = Query(..., description="종료 날짜"),
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile)
) -> SummaryResponse:
    """
    회사의 출고 배송 요약을 조회합니다.
    """
    request = SummaryRequest(
        start_date=start_date,
        end_date=end_date,
        direction=Direction.OUTBOUND,
        transaction_type=TransactionType.SHIPMENT,
        company_id=current_profile.company_id
    )
    
    return services.get_daily_summary_by_request(db, request)

@router.get("/shipments/inbound", response_model=SummaryResponse)
def get_shipment_inbound_summary(
    start_date: date = Query(..., description="시작 날짜"),
    end_date: date = Query(..., description="종료 날짜"),
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile)
) -> SummaryResponse:
    """
    회사의 입고 배송 요약을 조회합니다.
    """
    request = SummaryRequest(
        start_date=start_date,
        end_date=end_date,
        direction=Direction.INBOUND,
        transaction_type=TransactionType.SHIPMENT,
        company_id=current_profile.company_id
    )
    
    return services.get_daily_summary_by_request(db, request) 