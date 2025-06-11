from datetime import date
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date, or_
from app.company.shipment_summary.schemas import ShipmentSummary, ShipmentSummaryRow
from app.transactions.common.models import ProductQuality
from app.transactions.wholesale_shipment.models import WholesaleShipment, WholesaleShipmentItem
from app.transactions.retail_shipment.models import RetailShipment, RetailShipmentItem
from uuid import UUID

def get_shipment_summary_by_date(db: Session, target_date: date, company_id: UUID) -> ShipmentSummary:
    # 도매 출하 데이터 조회 (내 회사가 공급자이거나 수신자인 경우)
    wholesale_rows = db.query(
        cast(WholesaleShipment.shipment_datetime, Date).label('shipment_date'),
        WholesaleShipment.departure_center_id.label('center_id'),
        WholesaleShipmentItem.product_name,
        func.literal('도매').label('shipment_type'),
        WholesaleShipmentItem.quality,
        WholesaleShipmentItem.quantity,
        WholesaleShipment.arrival_center_id.label('destination')
    ).join(
        WholesaleShipmentItem,
        WholesaleShipment.id == WholesaleShipmentItem.shipment_id
    ).filter(
        cast(WholesaleShipment.shipment_datetime, Date) == target_date,
        or_(
            WholesaleShipment.supplier_company_id == company_id,
            WholesaleShipment.receiver_company_id == company_id
        )
    ).all()

    # 소매 출하 데이터 조회 (내 회사가 공급자이거나 수신자인 경우)
    retail_rows = db.query(
        cast(RetailShipment.shipment_datetime, Date).label('shipment_date'),
        RetailShipment.departure_center_id.label('center_id'),
        RetailShipmentItem.product_name,
        func.literal('소매').label('shipment_type'),
        RetailShipmentItem.quality,
        RetailShipmentItem.quantity,
        RetailShipment.arrival_center_id.label('destination')
    ).join(
        RetailShipmentItem,
        RetailShipment.id == RetailShipmentItem.shipment_id
    ).filter(
        cast(RetailShipment.shipment_datetime, Date) == target_date,
        or_(
            RetailShipment.supplier_company_id == company_id,
            RetailShipment.receiver_company_id == company_id
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