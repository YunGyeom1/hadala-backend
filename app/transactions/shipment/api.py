from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
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

def check_shipment_permission(
    db: Session,
    shipment_id: Optional[UUID],
    profile: Profile,
    expected_roles: Optional[List[ProfileRole]] = None
) -> None:
    """
    출하 데이터에 대한 권한을 확인합니다.
    
    Args:
        db: 데이터베이스 세션
        shipment_id: 확인할 출하 데이터 ID (None인 경우 생성 권한만 확인)
        profile: 현재 사용자 프로필
        expected_roles: 권한 확인 기준 역할 목록
    
    Raises:
        HTTPException: 권한이 없는 경우
    """
    # 역할 권한 확인
    if expected_roles and profile.role not in expected_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Required roles: {[role.value for role in expected_roles]}"
        )
    
    # 특정 shipment에 대한 권한 확인
    if shipment_id:
        shipment = crud.get_shipment(db, shipment_id)
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Shipment not found"
            )
        
        # 회사 권한 확인 (공급자 또는 수신자)
        if (profile.company_id != shipment.supplier_company_id and 
            profile.company_id != shipment.receiver_company_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this shipment"
            )

@router.get("/{shipment_id}", response_model=ShipmentResponse)
def read_shipment(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile)
):
    """
    특정 출하 데이터를 조회합니다.
    
    Args:
        shipment_id: 출하 데이터 ID
        db: 데이터베이스 세션
        current_profile: 현재 사용자 프로필
    
    Returns:
        ShipmentResponse: 출하 데이터 상세 정보
    
    Raises:
        HTTPException: 권한이 없거나 데이터가 없는 경우
    """
    check_shipment_permission(
        db, shipment_id, current_profile, 
        expected_roles=[ProfileRole.owner, ProfileRole.manager, ProfileRole.member]
    )
    
    shipment = crud.get_shipment_with_details(db, shipment_id)
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Shipment not found"
        )
    return shipment

@router.get("/", response_model=ShipmentListResponse)
def list_shipments(
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile),
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="가져올 항목 수"),
    start_date: Optional[datetime] = Query(None, description="시작 날짜"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜"),
    shipment_status: Optional[str] = Query(None, description="출하 상태"),
    is_supplier: Optional[bool] = Query(None, description="공급자 여부")
):
    """
    출하 데이터 목록을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        current_profile: 현재 사용자 프로필
        skip: 건너뛸 항목 수
        limit: 가져올 항목 수 (최대 1000)
        start_date: 시작 날짜
        end_date: 종료 날짜
        shipment_status: 출하 상태
        is_supplier: 공급자 여부
    
    Returns:
        ShipmentListResponse: 출하 데이터 목록과 총 개수
    """
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
    items = []
    for shipment in shipments:
        detailed_shipment = crud.get_shipment_with_details(db, shipment.id)
        if detailed_shipment:
            items.append(detailed_shipment)
    return {
        "shipments": items,
        "total": total,
        "page": skip // limit + 1 if limit else 1,
        "size": limit
    }

@router.post("/", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
def create_shipment(
    shipment: ShipmentCreate,
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile)
):
    """
    새로운 출하 데이터를 생성합니다.
    
    Args:
        shipment: 생성할 출하 데이터
        db: 데이터베이스 세션
        current_profile: 현재 사용자 프로필
    
    Returns:
        ShipmentResponse: 생성된 출하 데이터
    
    Raises:
        HTTPException: 권한이 없거나 생성에 실패한 경우
    """
    check_shipment_permission(
        db, None, current_profile, 
        expected_roles=[ProfileRole.owner, ProfileRole.manager]
    )
    
    try:
        db_shipment = crud.create_shipment(db, shipment, current_profile.username)
        if not db_shipment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Failed to create shipment"
            )
        
        return crud.get_shipment_with_details(db, db_shipment.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create shipment: {str(e)}"
        )

@router.put("/{shipment_id}", response_model=ShipmentResponse)
def update_shipment(
    shipment_id: UUID,
    shipment: ShipmentUpdate,
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile)
):
    """
    출하 데이터를 업데이트합니다.
    
    Args:
        shipment_id: 업데이트할 출하 데이터 ID
        shipment: 업데이트할 데이터
        db: 데이터베이스 세션
        current_profile: 현재 사용자 프로필
    
    Returns:
        ShipmentResponse: 업데이트된 출하 데이터
    
    Raises:
        HTTPException: 권한이 없거나 업데이트에 실패한 경우
    """
    check_shipment_permission(
        db, shipment_id, current_profile, 
        expected_roles=[ProfileRole.owner, ProfileRole.manager]
    )
    
    try:
        db_shipment = crud.update_shipment(db, shipment_id, shipment)
        if not db_shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Shipment not found"
            )
        
        return crud.get_shipment_with_details(db, db_shipment.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update shipment: {str(e)}"
        )

@router.delete("/{shipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shipment(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile)
):
    """
    출하 데이터를 삭제합니다.
    
    Args:
        shipment_id: 삭제할 출하 데이터 ID
        db: 데이터베이스 세션
        current_profile: 현재 사용자 프로필
    
    Raises:
        HTTPException: 권한이 없거나 삭제에 실패한 경우
    """
    check_shipment_permission(
        db, shipment_id, current_profile, 
        expected_roles=[ProfileRole.owner, ProfileRole.manager]
    )
    
    try:
        if not crud.delete_shipment(db, shipment_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Shipment not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete shipment: {str(e)}"
        ) 