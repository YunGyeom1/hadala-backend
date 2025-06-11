from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.database.session import get_db
from app.profile.dependencies import get_current_profile
from app.profile.models import Profile
from . import crud, schemas
from app.transactions.common.permissions import check_shipment_access
from app.transactions.common import schemas as common_schemas

router = APIRouter(prefix="/wholesale-shipments", tags=["wholesale-shipments"])

@router.post("/", response_model=schemas.WholesaleShipmentResponse)
def create_wholesale_shipment(
    shipment_create: schemas.WholesaleShipmentCreate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    새로운 도매 출하를 생성합니다.
    """
    if not current_profile.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="회사 소속이 아닙니다"
        )
    
    return crud.create_wholesale_shipment(db, shipment_create, current_profile.id)

@router.get("/search", response_model=schemas.PaginatedResponse)
def search_wholesale_shipments(
    search_params: schemas.WholesaleShipmentSearch = Depends(),
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    도매 출하를 검색합니다.
    """
    if not current_profile.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="회사 소속이 아닙니다"
        )
    
    shipments, total = crud.search_wholesale_shipments(db, search_params, current_profile.company_id)
    return schemas.PaginatedResponse.create(
        items=shipments,
        total=total,
        page=search_params.page,
        page_size=search_params.page_size
    )

@router.get("/{shipment_id}", response_model=schemas.WholesaleShipmentResponse)
def get_wholesale_shipment(
    shipment_id: UUID,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    특정 도매 출하를 조회합니다.
    """
    shipment = check_shipment_access(db, shipment_id, current_profile, require_ownership=False)
    return shipment

@router.get("/{shipment_id}/items", response_model=List[schemas.WholesaleShipmentItemResponse])
def get_shipment_items(
    shipment_id: UUID,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    출하의 아이템 리스트를 조회합니다.
    """
    check_shipment_access(db, shipment_id, current_profile, require_ownership=False)
    return crud.get_wholesale_shipment_items(db, shipment_id)

@router.put("/{shipment_id}", response_model=schemas.WholesaleShipmentResponse)
def update_wholesale_shipment(
    shipment_id: UUID,
    shipment_update: schemas.WholesaleShipmentUpdate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    도매 출하를 수정합니다.
    """
    check_shipment_access(db, shipment_id, current_profile, require_ownership=True)
    updated_shipment = crud.update_wholesale_shipment(db, shipment_id, shipment_update)
    return updated_shipment

@router.patch("/{shipment_id}/status", response_model=schemas.WholesaleShipmentResponse)
def update_shipment_status(
    shipment_id: UUID,
    status_update: common_schemas.ShipmentStatusUpdate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    출하 상태를 변경합니다.
    """
    check_shipment_access(db, shipment_id, current_profile, require_ownership=True)
    updated_shipment = crud.update_wholesale_shipment_status(db, shipment_id, status_update)
    return updated_shipment

@router.patch("/{shipment_id}/payment-status", response_model=schemas.WholesaleShipmentResponse)
def update_payment_status(
    shipment_id: UUID,
    status_update: common_schemas.PaymentStatusUpdate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    결제 상태를 변경합니다.
    """
    check_shipment_access(db, shipment_id, current_profile, require_ownership=True)
    updated_shipment = crud.update_wholesale_shipment_payment_status(db, shipment_id, status_update)
    return updated_shipment

@router.delete("/{shipment_id}")
def delete_wholesale_shipment(
    shipment_id: UUID,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    도매 출하를 삭제합니다.
    """
    check_shipment_access(db, shipment_id, current_profile, require_ownership=True)
    if not crud.delete_wholesale_shipment(db, shipment_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="출하 삭제에 실패했습니다"
        )

    return {"message": "출하가 삭제되었습니다"}

@router.delete("/{shipment_id}/items/{item_id}")
def delete_shipment_item(
    shipment_id: UUID,
    item_id: UUID,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    출하의 특정 아이템을 삭제합니다.
    """
    check_shipment_access(db, shipment_id, current_profile, require_ownership=True)
    if not crud.delete_wholesale_shipment_item(db, shipment_id, item_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="아이템 삭제에 실패했습니다"
        )
    
    return {"message": "아이템이 삭제되었습니다"} 