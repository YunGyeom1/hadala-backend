from datetime import date
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date, or_
from app.company.shipment_summary.schemas import ShipmentSummary, ShipmentSummaryRow
from app.transactions.common.models import ProductQuality
from app.transactions.shipment.models import shipment, shipmentItem
from uuid import UUID

def get_shipment_summary_by_date(db: Session, target_date: date, company_id: UUID) -> ShipmentSummary:
    # 도매 출하 데이터 조회 (내 회사가 공급자이거나 수신자인 경우)
    wholesale_rows = db.query(
        cast(shipment.shipment_datetime, Date).label('shipment_date'),
        shipment.departure_center_id.label('center_id'),
        shipmentItem.product_name,
        func.literal('도매').label('shipment_type'),
        shipmentItem.quality,
        shipmentItem.quantity,
        shipment.arrival_center_id.label('destination')
    ).join(
        shipmentItem,
        shipment.id == shipmentItem.shipment_id
    ).filter(
        cast(shipment.shipment_datetime, Date) == target_date,
        or_(
            shipment.supplier_company_id == company_id,
            shipment.receiver_company_id == company_id
        )
    ).all()

    # 소매 출하 데이터 조회 (내 회사가 공급자이거나 수신자인 경우)
    retail_rows = db.query(
        cast(shipment.shipment_datetime, Date).label('shipment_date'),
        shipment.departure_center_id.label('center_id'),
        shipmentItem.product_name,
        func.literal('소매').label('shipment_type'),
        shipmentItem.quality,
        shipmentItem.quantity,
        shipment.arrival_center_id.label('destination')
    ).join(
        shipmentItem,
        shipment.id == shipmentItem.shipment_id
    ).filter(
        cast(shipment.shipment_datetime, Date) == target_date,
        or_(
            shipment.supplier_company_id == company_id,
            shipment.receiver_company_id == company_id
        )
    ).all()

    # 결과 변환
    summary_rows = []
    for row in wholesale_rows + retail_rows:
        summary_rows.append(
            ShipmentSummaryRow(
                shipment_date=row.shipment_date,
                center_name=row.center_id,  # TODO: center_id를 center_name으로 변환 필요
                product_name=row.product_name,
                shipment_type=row.shipment_type,
                quality=row.quality,
                quantity=row.quantity,
                destination=row.destination  # TODO: center_id를 center_name으로 변환 필요
            )
        )

    return ShipmentSummary(rows=summary_rows)

def get_shipment_summary_by_date_range(
    db: Session, 
    start_date: date, 
    end_date: date,
    company_id: UUID
) -> List[ShipmentSummary]:
    summaries = []
    current_date = start_date
    
    while current_date <= end_date:
        summary = get_shipment_summary_by_date(db, current_date, company_id)
        if summary.rows:  # 해당 날짜에 데이터가 있는 경우만 추가
            summaries.append(summary)
        current_date = current_date.replace(day=current_date.day + 1)
    
    return summaries