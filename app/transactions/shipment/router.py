from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.profile.models import Profile, ProfileRole
from app.profile.dependencies import get_current_profile
from app.transactions.shipment import crud
from app.transactions.shipment.schemas import (
    ShipmentCreate, ShipmentUpdate, ShipmentResponse,
    ShipmentListResponse
)

router = APIRouter(prefix="/shipments", tags=["shipments"])

def check_permission(
    db: Session,
    shipment_id: Optional[UUID],
    profile: Profile,
    expected_role: Optional[List[ProfileRole]] = None
) -> None:
    """
    출하 데이터에 대한 권한을 확인합니다.
    
    Args:
        db: 데이터베이스 세션
        shipment_id: 확인할 출하 데이터 ID
        profile: 현재 사용자 프로필
        expected_role: 권한 확인 기준 역할 목록
    
    Raises:
        HTTPException: 권한이 없는 경우
    """
    if shipment_id:
        shipment = crud.get_shipment(db, shipment_id)
        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found")
    else:
        shipment = None
    
    # 사용자의 회사 확인
    if shipment and profile.company_id != shipment.supplier_company_id and profile.company_id != shipment.receiver_company_id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this shipment"
        )
    
    # 권한 확인
    if expected_role and profile.role not in expected_role:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this shipment"
        )

@router.get("/{shipment_id}", response_model=ShipmentResponse)
def read_shipment(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile)
):
    """특정 출하 데이터를 조회합니다."""
    check_permission(db, shipment_id, current_profile, expected_role=[ProfileRole.owner, ProfileRole.manager, ProfileRole.member])
    shipment = crud.get_shipment_with_details(db, shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment

@router.get("/", response_model=ShipmentListResponse)
def list_shipments(
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile),
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    shipment_status: Optional[str] = None,
    is_supplier: Optional[bool] = None
):
    """출하 데이터 목록을 조회합니다."""
    # 사용자의 회사 ID로 필터링
    company_id = current_profile.company_id
    
    shipments, total = crud.get_shipments(
        db=db,
        skip=skip,
        limit=limit,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
        shipment_status=shipment_status,
        is_supplier=is_supplier
    )
    
    return {
        "items": [
            crud.get_shipment_with_details(db, shipment.id)
            for shipment in shipments
        ],
        "total": total
    }

@router.post("/", response_model=ShipmentResponse)
def create_shipment(
    shipment: ShipmentCreate,
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile)
):
    """새로운 출하 데이터를 생성합니다."""
    check_permission(db, None, current_profile, expected_role=[ProfileRole.owner, ProfileRole.manager])
    
    db_shipment = crud.create_shipment(db, shipment, current_profile.username)
    if not db_shipment:
        raise HTTPException(status_code=400, detail="Failed to create shipment")
    return crud.get_shipment_with_details(db, db_shipment.id)

@router.put("/{shipment_id}", response_model=ShipmentResponse)
def update_shipment(
    shipment_id: UUID,
    shipment: ShipmentUpdate,
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile)
):
    """출하 데이터를 업데이트합니다."""
    check_permission(db, shipment_id, current_profile, expected_role=[ProfileRole.owner, ProfileRole.manager])
    
    db_shipment = crud.update_shipment(db, shipment_id, shipment)
    if not db_shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return crud.get_shipment_with_details(db, db_shipment.id)

@router.delete("/{shipment_id}")
def delete_shipment(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile)
):
    """출하 데이터를 삭제합니다."""
    check_permission(db, shipment_id, current_profile, expected_role=[ProfileRole.owner, ProfileRole.manager])
    
    if not crud.delete_shipment(db, shipment_id):
        raise HTTPException(status_code=404, detail="Shipment not found")
    return {"message": "Shipment deleted successfully"} 