from datetime import date, datetime
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from collections import defaultdict
from uuid import UUID

from app.transactions.summary.schemas import (
    CenterItem, CenterSummary, DailySummary, SummaryRequest, SummaryResponse,
    TransactionType, Direction
)
from app.transactions.summary.crud import (
    get_contracts_by_date_and_company,
    get_shipments_by_date_and_company
)


def get_daily_summary_by_request(
    db: Session,
    request: SummaryRequest
) -> SummaryResponse:
    """
    SummaryRequest를 처리하여 일자별 종합 데이터를 반환합니다.
    """
    # 1. SummaryRequest 처리
    daily_summaries = process_summary_request(db, request)
    
    # 2. SummaryResponse 생성 및 반환
    return SummaryResponse(
        start_date=request.start_date,
        end_date=request.end_date,
        direction=request.direction,
        transaction_type=request.transaction_type,
        daily_summaries=daily_summaries
    )


def process_summary_request(
    db: Session,
    request: SummaryRequest
) -> List[DailySummary]:
    """
    SummaryRequest를 처리하여 매일자 DailySummary를 생성합니다.
    """
    # 날짜 범위 생성
    date_range = generate_date_range(request.start_date, request.end_date)
    
    # 매일자 DailySummary 생성
    daily_summaries = []
    for current_date in date_range:
        daily_summary = create_daily_summary(db, request, current_date)
        if daily_summary:  # 데이터가 있는 경우만 추가
            daily_summaries.append(daily_summary)
    
    return daily_summaries


def generate_date_range(start_date: date, end_date: date) -> List[date]:
    """
    시작일부터 종료일까지의 날짜 리스트를 생성합니다.
    """
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date)
        current_date = current_date.replace(day=current_date.day + 1)
    return date_list


def create_daily_summary(
    db: Session,
    request: SummaryRequest,
    target_date: date
) -> Optional[DailySummary]:
    """
    특정 날짜의 DailySummary를 생성합니다.
    """
    # 그날 회사 센터별 Summary 종합
    center_summaries = get_center_summaries_for_date(db, request, target_date)
    
    # 데이터가 없으면 None 반환
    if not center_summaries:
        return None
    
    return DailySummary(
        date=target_date,
        center_summaries=center_summaries
    )


def get_center_summaries_for_date(
    db: Session,
    request: SummaryRequest,
    target_date: date
) -> List[CenterSummary]:
    """
    특정 날짜의 회사 센터별 Summary를 종합합니다.
    """
    if request.transaction_type == TransactionType.CONTRACT:
        results = get_contracts_by_date_and_company(
            db, target_date, request.company_id, request.direction
        )
    elif request.transaction_type == TransactionType.SHIPMENT:
        results = get_shipments_by_date_and_company(
            db, target_date, request.company_id, request.direction
        )
    else:
        raise ValueError(f"Unsupported transaction type: {request.transaction_type}")
    
    # CenterSummary 리스트 생성
    return create_center_summaries_from_results(results, request.direction)


def create_center_summaries_from_results(
    results: List,
    direction: Direction
) -> List[CenterSummary]:
    """
    쿼리 결과로부터 CenterSummary 리스트를 생성합니다.
    """
    # 센터별로 그룹화
    center_groups = defaultdict(list)
    
    for result in results:
        # 센터 이름 사용
        center_name = result.center_name
        
        center_item = CenterItem(
            product_name=result.product_name,
            quality=result.quality,
            quantity=int(result.total_quantity)
        )
        
        center_groups[center_name].append(center_item)
    
    # CenterSummary 리스트 생성
    center_summaries = []
    
    for center_name, items in center_groups.items():
        center_summary = CenterSummary(
            center_name=center_name,
            items=items
        )
        center_summaries.append(center_summary)
    
    return center_summaries 