from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.company.common.crud import get_company_by_name
from app.profile.crud import get_profile_by_username
from app.transactions.shipment.models import Shipment, ShipmentItem
from app.transactions.shipment.schemas import (
    ShipmentCreate, ShipmentUpdate, ShipmentResponse,
    ShipmentItemCreate, ShipmentItemResponse
)
from app.profile.models import Profile
from app.company.common.models import Company

def get_shipment(db: Session, shipment_id: UUID) -> Optional[Shipment]:
    """특정 출하 데이터를 조회합니다."""
    return db.query(Shipment).filter(Shipment.id == shipment_id).first()


def get_shipments(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    company_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    shipment_status: Optional[str] = None,
    is_supplier: Optional[bool] = None
) -> Tuple[List[Shipment], int]:
    """출하 데이터 목록을 조회합니다."""
    query = db.query(Shipment)
    
    # 필터 조건 적용
    if company_id:
        if is_supplier is not None:
            if is_supplier:
                query = query.filter(Shipment.supplier_company_id == company_id)
            else:
                query = query.filter(Shipment.receiver_company_id == company_id)
        else:
            query = query.filter(
                or_(
                    Shipment.supplier_company_id == company_id,
                    Shipment.receiver_company_id == company_id
                )
            )
    if start_date:
        query = query.filter(Shipment.shipment_datetime >= start_date)
    if end_date:
        query = query.filter(Shipment.shipment_datetime <= end_date)
    if shipment_status:
        query = query.filter(Shipment.shipment_status == shipment_status)
    
    # 전체 개수 조회
    total = query.count()
    
    # 페이지네이션 적용
    shipments = query.offset(skip).limit(limit).all()
    
    return shipments, total


def get_profile_id_by_username(db: Session, username: str) -> Optional[UUID]:
    """사용자 이름으로 프로필 ID를 조회합니다."""
    profile = db.query(Profile).filter(Profile.username == username).first()
    return profile.id if profile else None


def create_shipment(db: Session, shipment: ShipmentCreate, creator_username: str) -> Optional[Shipment]:
    """새로운 출하 데이터를 생성합니다."""
    # creator_id 조회
    creator_id = get_profile_by_username(db, creator_username).id
    if not creator_id:
        return None
    
    # 출하 데이터 생성
    db_shipment = Shipment(
        title=shipment.title,
        contract_id=shipment.contract_id,
        creator_id=creator_id,
        supplier_person_id=shipment.supplier_person_id,
        supplier_company_id=shipment.supplier_company_id,
        receiver_person_id=shipment.receiver_person_id,
        receiver_company_id=shipment.receiver_company_id,
        shipment_datetime=shipment.shipment_datetime,
        departure_center_id=shipment.departure_center_id,
        arrival_center_id=shipment.arrival_center_id,
        shipment_status=shipment.shipment_status,
        notes=shipment.notes
    )
    db.add(db_shipment)
    db.flush()
    
    # 출하 아이템 생성
    total_price = 0
    for item in shipment.items:
        item_total_price = item.quantity * item.unit_price
        db_item = ShipmentItem(
            shipment_id=db_shipment.id,
            product_name=item.product_name,
            quality=item.quality,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item_total_price
        )
        db.add(db_item)
        total_price += item_total_price
    
    # 총 가격 업데이트
    db_shipment.total_price = total_price
    db.commit()
    db.refresh(db_shipment)
    
    return db_shipment


def update_shipment(
    db: Session,
    shipment_id: UUID,
    shipment_update: ShipmentUpdate
) -> Optional[Shipment]:
    """출하 데이터를 업데이트합니다."""
    db_shipment = get_shipment(db, shipment_id)
    if not db_shipment:
        return None
    
    # 기본 필드 업데이트
    update_data = shipment_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field not in ["items"]:
            setattr(db_shipment, field, value)
        
    # 아이템 업데이트
    if shipment_update.items is not None:
        # 기존 아이템 삭제
        db.query(ShipmentItem).filter(ShipmentItem.shipment_id == shipment_id).delete()
        
        # 새로운 아이템 추가
        total_price = 0
        for item in shipment_update.items:
            item_total_price = item.quantity * item.unit_price
            db_item = ShipmentItem(
                shipment_id=db_shipment.id,
                product_name=item.product_name,
                quality=item.quality,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item_total_price
            )
            db.add(db_item)
            total_price += item_total_price
    
    # 총 가격 업데이트
    db_shipment.total_price = total_price
    
    db.commit()
    db.refresh(db_shipment)
    return db_shipment


def delete_shipment(db: Session, shipment_id: UUID) -> bool:
    """출하 데이터를 삭제합니다."""
    db_shipment = get_shipment(db, shipment_id)
    if not db_shipment:
        return False
    
    db.delete(db_shipment)
    db.commit()
    return True


def get_shipment_with_details(db: Session, shipment_id: UUID) -> Optional[ShipmentResponse]:
    """출하 데이터와 관련 상세 정보를 조회합니다."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        return None
    
    # 관계 데이터 로드
    db.refresh(shipment)
    
    # 응답 데이터 구성
    return ShipmentResponse(
        id=shipment.id,
        title=shipment.title,
        contract_id=shipment.contract_id,
        supplier_person_id=shipment.supplier_person_id,
        supplier_company_id=shipment.supplier_company_id,
        receiver_person_id=shipment.receiver_person_id,
        receiver_company_id=shipment.receiver_company_id,
        departure_center_id=shipment.departure_center_id,
        arrival_center_id=shipment.arrival_center_id,
        shipment_datetime=shipment.shipment_datetime,
        shipment_status=shipment.shipment_status,
        notes=shipment.notes,
        creator_id=shipment.creator_id,
        items=[
            ShipmentItemResponse(
                id=item.id,
                product_name=item.product_name,
                quality=item.quality,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                created_at=item.created_at,
                updated_at=item.updated_at
            ) for item in shipment.items
        ]
    ) 