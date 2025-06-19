from datetime import date, datetime
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from collections import defaultdict
from uuid import UUID

from app.transactions.contract.models import Contract, ContractItem
from app.transactions.shipment.models import Shipment, ShipmentItem
from app.transactions.contract.schemas import ContractResponse
from app.transactions.summary.schemas import (
    CenterItem, CenterSummary, DailySummary, SummaryRequest, SummaryResponse,
    TransactionType, Direction
)
from app.transactions.common.models import ProductQuality, ContractStatus

def get_contracts_by_date_and_company(
    db: Session,
    target_date: date,
    company_id: UUID,
    direction: Direction
) -> List:
    """
    특정 날짜와 회사의 계약 데이터를 조회합니다.
    """
    # 방향에 따라 센터 필드 선택
    center_field = Contract.departure_center_id if direction == Direction.OUTBOUND else Contract.arrival_center_id
    
    query = db.query(
        center_field,
        ContractItem.product_name,
        ContractItem.quality,
        func.sum(ContractItem.quantity).label('total_quantity')
    ).join(
        ContractItem, Contract.id == ContractItem.contract_id
    ).filter(
        func.date(Contract.delivery_datetime) == target_date
    )
    
    # 회사 필터 적용
    if direction == Direction.OUTBOUND:
        query = query.filter(Contract.supplier_company_id == company_id)
    else:
        query = query.filter(Contract.receiver_company_id == company_id)
    
    # 센터, 상품, 품질별로 그룹화
    query = query.group_by(
        center_field,
        ContractItem.product_name,
        ContractItem.quality
    )
    
    return query.all()


def get_shipments_by_date_and_company(
    db: Session,
    target_date: date,
    company_id: UUID,
    direction: Direction
) -> List:
    """
    특정 날짜와 회사의 배송 데이터를 조회합니다.
    """
    # 방향에 따라 센터 필드 선택
    center_field = Shipment.departure_center_id if direction == Direction.OUTBOUND else Shipment.arrival_center_id
    
    query = db.query(
        center_field,
        ShipmentItem.product_name,
        ShipmentItem.quality,
        func.sum(ShipmentItem.quantity).label('total_quantity')
    ).join(
        ShipmentItem, Shipment.id == ShipmentItem.shipment_id
    ).filter(
        func.date(Shipment.shipment_datetime) == target_date
    )
    
    # 회사 필터 적용
    if direction == Direction.OUTBOUND:
        query = query.filter(Shipment.supplier_company_id == company_id)
    else:
        query = query.filter(Shipment.receiver_company_id == company_id)
    
    # 센터, 상품, 품질별로 그룹화
    query = query.group_by(
        center_field,
        ShipmentItem.product_name,
        ShipmentItem.quality
    )
    
    return query.all()
