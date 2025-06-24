from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.profile.models import Profile, ProfileRole
from app.profile.dependencies import get_current_profile
from app.transactions.contract import crud
from app.transactions.contract.schemas import (
    ContractCreate, ContractUpdate, ContractResponse,
    ContractStatus, PaymentStatus,
    ContractStatusUpdate, PaymentStatusUpdate
)

router = APIRouter(prefix="/contracts", tags=["contracts"])

def check_contract_permission(
    db: Session,
    contract_id: Optional[UUID],
    profile: Profile,
    expected_roles: Optional[List[ProfileRole]] = None
) -> None:
    """
    계약 데이터에 대한 권한을 확인합니다.
    
    Args:
        db: 데이터베이스 세션
        contract_id: 확인할 계약 데이터 ID (None인 경우 생성 권한만 확인)
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
    
    # 특정 contract에 대한 권한 확인
    if contract_id:
        contract = crud.get_contract(db, contract_id)
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Contract not found"
            )
        
        # 회사 권한 확인 (공급자 또는 수신자)
        if (profile.company_id != contract.supplier_company_id and 
            profile.company_id != contract.receiver_company_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this contract"
            )

@router.get("/{contract_id}", response_model=ContractResponse)
def read_contract(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile)
):
    """
    특정 계약 데이터를 조회합니다.
    
    Args:
        contract_id: 계약 데이터 ID
        db: 데이터베이스 세션
        current_profile: 현재 사용자 프로필
    
    Returns:
        ContractResponse: 계약 데이터 상세 정보
    
    Raises:
        HTTPException: 권한이 없거나 데이터가 없는 경우
    """
    check_contract_permission(
        db, contract_id, current_profile, 
        expected_roles=[ProfileRole.owner, ProfileRole.manager, ProfileRole.member]
    )
    
    contract = crud.get_contract_with_details(db, contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Contract not found"
        )
    return contract

@router.get("/", response_model=List[ContractResponse])
def list_contracts(
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile),
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="가져올 항목 수"),
    start_date: Optional[datetime] = Query(None, description="시작 날짜"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜"),
    contract_status: Optional[str] = Query(None, description="계약 상태"),
    is_supplier: Optional[bool] = Query(None, description="공급자 여부")
):
    """
    계약 데이터 목록을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        current_profile: 현재 사용자 프로필
        skip: 건너뛸 항목 수
        limit: 가져올 항목 수 (최대 1000)
        start_date: 시작 날짜
        end_date: 종료 날짜
        contract_status: 계약 상태
        is_supplier: 공급자 여부
    
    Returns:
        List[ContractResponse]: 계약 데이터 목록
    """
    # 사용자의 회사 ID로 필터링
    company_id = current_profile.company_id
    
    contracts, total = crud.get_contracts(
        db=db,
        skip=skip,
        limit=limit,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
        contract_status=contract_status,
        is_supplier=is_supplier
    )
    
    # 상세 정보 포함하여 반환
    items = []
    for contract in contracts:
        detailed_contract = crud.get_contract_with_details(db, contract.id)
        if detailed_contract:
            items.append(detailed_contract)
    
    return items

@router.post("/", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    contract: ContractCreate,
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile)
):
    """
    새로운 계약 데이터를 생성합니다.
    
    Args:
        contract: 생성할 계약 데이터
        db: 데이터베이스 세션
        current_profile: 현재 사용자 프로필
    
    Returns:
        ContractResponse: 생성된 계약 데이터
    
    Raises:
        HTTPException: 권한이 없거나 생성에 실패한 경우
    """
    check_contract_permission(
        db, None, current_profile, 
        expected_roles=[ProfileRole.owner, ProfileRole.manager]
    )
    
    try:
        db_contract = crud.create_contract(db, contract, current_profile.username)
        if not db_contract:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Failed to create contract"
            )
        
        return crud.get_contract_with_details(db, db_contract.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create contract: {str(e)}"
        )

@router.put("/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: UUID,
    contract: ContractUpdate,
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile)
):
    """
    계약 데이터를 업데이트합니다.
    
    Args:
        contract_id: 업데이트할 계약 데이터 ID
        contract: 업데이트할 데이터
        db: 데이터베이스 세션
        current_profile: 현재 사용자 프로필
    
    Returns:
        ContractResponse: 업데이트된 계약 데이터
    
    Raises:
        HTTPException: 권한이 없거나 업데이트에 실패한 경우
    """
    check_contract_permission(
        db, contract_id, current_profile, 
        expected_roles=[ProfileRole.owner, ProfileRole.manager]
    )
    
    try:
        db_contract = crud.update_contract(db, contract_id, contract)
        if not db_contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Contract not found"
            )
        
        return crud.get_contract_with_details(db, db_contract.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update contract: {str(e)}"
        )

@router.patch("/{contract_id}/status", response_model=ContractResponse)
def update_contract_status(
    contract_id: UUID,
    status_update: ContractStatusUpdate,
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile)
):
    """
    계약 상태를 업데이트합니다.
    
    Args:
        contract_id: 업데이트할 계약 데이터 ID
        status_update: 상태 업데이트 데이터
        db: 데이터베이스 세션
        current_profile: 현재 사용자 프로필
    
    Returns:
        ContractResponse: 업데이트된 계약 데이터
    
    Raises:
        HTTPException: 권한이 없거나 업데이트에 실패한 경우
    """
    check_contract_permission(
        db, contract_id, current_profile, 
        expected_roles=[ProfileRole.owner, ProfileRole.manager]
    )
    
    try:
        db_contract = crud.update_contract_status(db, contract_id, status_update.contract_status)
        if not db_contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Contract not found"
            )
        
        return crud.get_contract_with_details(db, db_contract.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update contract status: {str(e)}"
        )

@router.patch("/{contract_id}/payment-status", response_model=ContractResponse)
def update_payment_status(
    contract_id: UUID,
    status_update: PaymentStatusUpdate,
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile)
):
    """
    결제 상태를 업데이트합니다.
    
    Args:
        contract_id: 업데이트할 계약 데이터 ID
        status_update: 결제 상태 업데이트 데이터
        db: 데이터베이스 세션
        current_profile: 현재 사용자 프로필
    
    Returns:
        ContractResponse: 업데이트된 계약 데이터
    
    Raises:
        HTTPException: 권한이 없거나 업데이트에 실패한 경우
    """
    check_contract_permission(
        db, contract_id, current_profile, 
        expected_roles=[ProfileRole.owner, ProfileRole.manager]
    )
    
    try:
        db_contract = crud.update_payment_status(db, contract_id, status_update.payment_status)
        if not db_contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Contract not found"
            )
        
        return crud.get_contract_with_details(db, db_contract.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update payment status: {str(e)}"
        )

@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_profile: Profile = Depends(get_current_profile)
):
    """
    계약 데이터를 삭제합니다.
    
    Args:
        contract_id: 삭제할 계약 데이터 ID
        db: 데이터베이스 세션
        current_profile: 현재 사용자 프로필
    
    Raises:
        HTTPException: 권한이 없거나 삭제에 실패한 경우
    """
    check_contract_permission(
        db, contract_id, current_profile, 
        expected_roles=[ProfileRole.owner, ProfileRole.manager]
    )
    
    try:
        if not crud.delete_contract(db, contract_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Contract not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete contract: {str(e)}"
        ) 