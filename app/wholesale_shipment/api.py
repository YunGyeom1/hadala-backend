from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date
from app.database.session import get_db
from app.core.auth.utils import get_current_user
from app.user.models import User
from . import crud, schemas

router = APIRouter(prefix="/wholesale-shipments", tags=["wholesale-shipments"])

@router.post("/", response_model=schemas.WholesaleShipment)
def create_shipment(
    shipment: schemas.WholesaleShipmentCreate,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """새 출고 기록 생성"""
    company_id = current_user.wholesale.company_id
    return crud.create_shipment(db, shipment, company_id)

@router.get("/", response_model=List[schemas.WholesaleShipment])
def get_shipments(
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    center_id: Optional[UUID] = None,
    farmer_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """출고 목록 조회"""
    company_id = current_user.wholesale.company_id
    return crud.get_shipments(
        db,
        company_id,
        skip=skip,
        limit=limit,
        center_id=center_id,
        farmer_id=farmer_id,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/{shipment_id}", response_model=schemas.WholesaleShipment)
def get_shipment(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """특정 출고 조회"""
    company_id = current_user.wholesale.company_id
    shipment = crud.get_shipment(db, shipment_id, company_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="출고를 찾을 수 없습니다.")
    return shipment

@router.put("/{shipment_id}", response_model=schemas.WholesaleShipment)
def update_shipment(
    shipment_id: UUID,
    shipment: schemas.WholesaleShipmentUpdate,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """출고 정보 수정"""
    company_id = current_user.wholesale.company_id
    updated_shipment = crud.update_shipment(db, shipment_id, shipment, company_id)
    if not updated_shipment:
        raise HTTPException(status_code=404, detail="출고를 찾을 수 없거나 수정할 수 없는 상태입니다.")
    return updated_shipment

@router.delete("/{shipment_id}")
def delete_shipment(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """출고 삭제"""
    company_id = current_user.wholesale.company_id
    if not crud.delete_shipment(db, shipment_id, company_id):
        raise HTTPException(status_code=404, detail="출고를 찾을 수 없거나 삭제할 수 없는 상태입니다.")
    return {"message": "출고가 삭제되었습니다."}

@router.get("/{shipment_id}/items", response_model=List[schemas.WholesaleShipmentItem])
def get_shipment_items(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """출고 품목 목록 조회"""
    company_id = current_user.wholesale.company_id
    items = crud.get_shipment_items(db, shipment_id, company_id)
    if not items:
        raise HTTPException(status_code=404, detail="출고를 찾을 수 없습니다.")
    return items

@router.put("/items/{item_id}", response_model=schemas.WholesaleShipmentItem)
def update_shipment_item(
    item_id: UUID,
    item: schemas.WholesaleShipmentItemUpdate,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """출고 품목 수정"""
    company_id = current_user.wholesale.company_id
    updated_item = crud.update_shipment_item(db, item_id, item, company_id)
    if not updated_item:
        raise HTTPException(status_code=404, detail="품목을 찾을 수 없거나 수정할 수 없는 상태입니다.")
    return updated_item

@router.delete("/items/{item_id}")
def delete_shipment_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """출고 품목 삭제"""
    company_id = current_user.wholesale.company_id
    if not crud.delete_shipment_item(db, item_id, company_id):
        raise HTTPException(status_code=404, detail="품목을 찾을 수 없거나 삭제할 수 없는 상태입니다.")
    return {"message": "품목이 삭제되었습니다."}

@router.get("/contracts/{contract_id}/shipments", response_model=List[schemas.WholesaleShipment])
def get_contract_shipments(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """계약에 연결된 출고 목록 조회"""
    company_id = current_user.wholesale.company_id
    shipments = crud.get_contract_shipments(db, contract_id, company_id)
    if not shipments:
        raise HTTPException(status_code=404, detail="계약을 찾을 수 없습니다.")
    return shipments

@router.post("/from-contract/{contract_id}", response_model=schemas.WholesaleShipment)
def create_shipment_from_contract(
    contract_id: UUID,
    shipment: schemas.WholesaleShipmentCreate,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """계약 기준으로 출고 생성"""
    company_id = current_user.wholesale.company_id
    new_shipment = crud.create_shipment_from_contract(db, contract_id, shipment, company_id)
    if not new_shipment:
        raise HTTPException(status_code=404, detail="계약을 찾을 수 없습니다.")
    return new_shipment

@router.get("/contracts/{contract_id}/shipment-progress", response_model=schemas.ContractShipmentProgress)
def get_contract_shipment_progress(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """계약 품목별 출고 이행 현황 조회"""
    company_id = current_user.wholesale.company_id
    progress = crud.get_contract_shipment_progress(db, contract_id, company_id)
    if not progress:
        raise HTTPException(status_code=404, detail="계약을 찾을 수 없습니다.")
    return progress

@router.post("/{shipment_id}/finalize", response_model=schemas.WholesaleShipment)
def finalize_shipment(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """출고 완료 처리"""
    company_id = current_user.wholesale.company_id
    shipment = crud.finalize_shipment(db, shipment_id, company_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="출고를 찾을 수 없거나 이미 완료된 상태입니다.")
    return shipment 