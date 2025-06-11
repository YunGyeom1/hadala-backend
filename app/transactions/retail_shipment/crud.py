from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.transactions.retail_shipment import models, schemas
from app.transactions.retail_contract.models import ContractStatus, PaymentStatus

def create_retail_shipment(
    db: Session,
    shipment_create: schemas.RetailShipmentCreate,
    creator_id: UUID
) -> schemas.RetailShipmentResponse:
    """
    새로운 소매 출하를 생성합니다.
    """
    # 출하 생성
    db_shipment = models.RetailShipment(
        title=shipment_create.title,
        contract_id=shipment_create.contract_id,
        creator_id=creator_id,
        supplier_person_id=shipment_create.supplier_person_id,
        supplier_company_id=shipment_create.supplier_company_id,
        receiver_person_id=shipment_create.receiver_person_id,
        receiver_company_id=shipment_create.receiver_company_id,
        shipment_datetime=shipment_create.shipment_datetime,
        departure_center_id=shipment_create.departure_center_id,
        arrival_center_id=shipment_create.arrival_center_id,
        payment_due_date=shipment_create.payment_due_date,
        notes=shipment_create.notes,
        total_price=0.0  # 초기값 설정
    )
    
    db.add(db_shipment)
    db.flush()  # ID 생성
    
    # 출하 항목 생성
    total_price = 0.0
    for item in shipment_create.items:
        db_item = models.RetailShipmentItem(
            shipment_id=db_shipment.id,
            contract_item_id=item.contract_item_id,
            product_name=item.product_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.quantity * item.unit_price,
            notes=item.notes
        )
        total_price += db_item.total_price
        db.add(db_item)
    
    # 총액 업데이트
    db_shipment.total_price = total_price
    
    db.commit()
    db.refresh(db_shipment)
    
    return schemas.RetailShipmentResponse.model_validate(db_shipment)

def get_retail_shipment(
    db: Session,
    shipment_id: UUID
) -> Optional[schemas.RetailShipmentResponse]:
    """
    ID로 출하를 조회합니다.
    """
    db_shipment = db.query(models.RetailShipment).filter(
        models.RetailShipment.id == shipment_id
    ).first()
    
    if not db_shipment:
        return None
        
    return schemas.RetailShipmentResponse.model_validate(db_shipment)

def search_retail_shipments(
    db: Session,
    search_params: schemas.RetailShipmentSearch
) -> Tuple[List[schemas.RetailShipmentResponse], int]:
    """
    검색 조건에 맞는 출하 목록을 조회합니다.
    """
    query = db.query(models.RetailShipment)
    
    # 검색 조건 적용
    if search_params.title:
        query = query.filter(models.RetailShipment.title.ilike(f"%{search_params.title}%"))
    
    if search_params.start_date:
        query = query.filter(models.RetailShipment.shipment_datetime >= search_params.start_date)
    
    if search_params.end_date:
        query = query.filter(models.RetailShipment.shipment_datetime <= search_params.end_date)
    
    if search_params.supplier_company_id:
        query = query.filter(models.RetailShipment.supplier_company_id == search_params.supplier_company_id)
    
    if search_params.receiver_company_id:
        query = query.filter(models.RetailShipment.receiver_company_id == search_params.receiver_company_id)
    
    if search_params.shipment_status:
        query = query.filter(models.RetailShipment.shipment_status == search_params.shipment_status)
    
    if search_params.payment_status:
        query = query.filter(models.RetailShipment.payment_status == search_params.payment_status)
    
    # 전체 개수 조회
    total = query.count()
    
    # 페이지네이션 적용
    query = query.order_by(models.RetailShipment.created_at.desc())
    query = query.offset((search_params.page - 1) * search_params.page_size)
    query = query.limit(search_params.page_size)
    
    # 결과 조회
    shipments = query.all()
    
    return [schemas.RetailShipmentResponse.model_validate(shipment) for shipment in shipments], total

def get_retail_shipment_items(
    db: Session,
    shipment_id: UUID
) -> List[schemas.RetailShipmentItemResponse]:
    """
    출하의 항목 목록을 조회합니다.
    """
    items = db.query(models.RetailShipmentItem).filter(
        models.RetailShipmentItem.shipment_id == shipment_id
    ).all()
    
    return [schemas.RetailShipmentItemResponse.model_validate(item) for item in items]

def update_retail_shipment(
    db: Session,
    shipment_id: UUID,
    shipment_update: schemas.RetailShipmentUpdate
) -> Optional[schemas.RetailShipmentResponse]:
    """
    출하 정보를 업데이트합니다.
    """
    db_shipment = get_retail_shipment(db, shipment_id)
    
    if not db_shipment:
        return None
    
    # 기본 정보 업데이트
    update_data = shipment_update.model_dump(exclude_unset=True, exclude={'items'})
    for key, value in update_data.items():
        setattr(db_shipment, key, value)

    if "items" in update_data:
        items = update_data.pop("items")
        
        # 기존 항목 삭제
        db.query(models.RetailShipmentItem).filter(
            models.RetailShipmentItem.shipment_id == shipment_id
        ).delete()
        
        # 새로운 항목 추가
        total_price = 0.0
        for item in items:
            db_item = models.RetailShipmentItem(
                shipment_id=shipment_id,
                contract_item_id=item.contract_item_id,
                product_name=item.product_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.quantity * item.unit_price,
                notes=item.notes
            )
            total_price += db_item.total_price
            db.add(db_item)
        
        db_shipment.total_price = total_price
    
    db.commit()
    db.refresh(db_shipment)
    
    return schemas.RetailShipmentResponse.model_validate(db_shipment)

def update_retail_shipment_status(
    db: Session,
    shipment_id: UUID,
    status: ContractStatus
) -> Optional[schemas.RetailShipmentResponse]:
    """
    출하 상태를 변경합니다.
    """
    db_shipment = get_retail_shipment(db, shipment_id)
    
    if not db_shipment:
        return None
    
    db_shipment.shipment_status = status
    db.commit()
    db.refresh(db_shipment)
    
    return schemas.RetailShipmentResponse.model_validate(db_shipment)

def update_retail_shipment_payment_status(
    db: Session,
    shipment_id: UUID,
    status: PaymentStatus
) -> Optional[schemas.RetailShipmentResponse]:
    """
    결제 상태를 변경합니다.
    """
    db_shipment = get_retail_shipment(db, shipment_id)
    
    if not db_shipment:
        return None
    
    db_shipment.payment_status = status
    db.commit()
    db.refresh(db_shipment)
    
    return schemas.RetailShipmentResponse.model_validate(db_shipment)

def delete_retail_shipment(
    db: Session,
    shipment_id: UUID
) -> bool:
    """
    출하를 삭제합니다.
    """
    db_shipment = get_retail_shipment(db, shipment_id)
    
    if not db_shipment:
        return False
    
    db.delete(db_shipment)
    db.commit()
    
    return True

def delete_retail_shipment_item(
    db: Session,
    shipment_id: UUID,
    item_id: UUID
) -> bool:
    """
    출하 항목을 삭제합니다.
    """
    db_item = db.query(models.RetailShipmentItem).filter(
        and_(
            models.RetailShipmentItem.shipment_id == shipment_id,
            models.RetailShipmentItem.id == item_id
        )
    ).first()
    
    if not db_item:
        return False
    
    # 총액 업데이트
    db_shipment = db.query(models.RetailShipment).filter(
        models.RetailShipment.id == shipment_id
    ).first()
    
    if db_shipment:
        db_shipment.total_price -= db_item.total_price
    
    db.delete(db_item)
    db.commit()
    
    return True 