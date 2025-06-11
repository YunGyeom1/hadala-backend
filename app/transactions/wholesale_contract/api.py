from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.database.session import get_db
from app.profile.dependencies import get_current_profile
from app.profile.models import Profile
from . import crud, schemas
from app.transactions.common.permissions import check_contract_access
from app.transactions.common import schemas as common_schemas

router = APIRouter(prefix="/wholesale-contracts", tags=["wholesale-contracts"])

@router.post("/", response_model=schemas.WholesaleContractResponse)
def create_wholesale_contract(
    contract_create: schemas.WholesaleContractCreate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    새로운 도매 계약을 생성합니다.
    """
    if not current_profile.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="회사 소속이 아닙니다"
        )
    
    return crud.create_wholesale_contract(db, contract_create, current_profile.id)

@router.get("/search", response_model=schemas.PaginatedResponse[schemas.WholesaleContractResponse])
def search_wholesale_contracts(
    search_params: schemas.WholesaleContractSearch = Depends(),
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    도매 계약을 검색합니다.
    """
    if not current_profile.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="회사 소속이 아닙니다"
        )
    
    contracts, total = crud.search_wholesale_contracts(db, search_params, current_profile.company_id)
    return schemas.PaginatedResponse.create(
        items=contracts,
        total=total,
        page=search_params.page,
        page_size=search_params.page_size
    )

@router.get("/{contract_id}", response_model=schemas.WholesaleContractResponse)
def get_wholesale_contract(
    contract_id: UUID,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    특정 도매 계약을 조회합니다.
    """
    contract = check_contract_access(db, contract_id, current_profile, require_ownership=False)
    return contract

@router.get("/{contract_id}/items", response_model=List[schemas.WholesaleContractItemResponse])
def get_contract_items(
    contract_id: UUID,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    계약의 아이템 리스트를 조회합니다.
    """
    check_contract_access(db, contract_id, current_profile, require_ownership=False)
    return crud.get_contract_items(db, contract_id)

@router.get("/{contract_id}/chain", response_model=List[schemas.WholesaleContractResponse])
def get_contract_chain(
    contract_id: UUID,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    연속 계약 리스트를 조회합니다.
    """
    check_contract_access(db, contract_id, current_profile, require_ownership=False)
    return crud.get_contract_chain(db, contract_id)

@router.put("/{contract_id}", response_model=schemas.WholesaleContractResponse)
def update_wholesale_contract(
    contract_id: UUID,
    contract_update: schemas.WholesaleContractUpdate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    도매 계약을 수정합니다.
    """
    check_contract_access(db, contract_id, current_profile, require_ownership=True)
    updated_contract = crud.update_wholesale_contract(db, contract_id, contract_update)
    return updated_contract

@router.patch("/{contract_id}/status", response_model=schemas.WholesaleContractResponse)
def update_contract_status(
    contract_id: UUID,
    status_update: common_schemas.ContractStatusUpdate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    계약 상태를 변경합니다.
    """
    check_contract_access(db, contract_id, current_profile, require_ownership=True)
    updated_contract = crud.update_contract_status(db, contract_id, status_update)
    return updated_contract

@router.patch("/{contract_id}/payment-status", response_model=schemas.WholesaleContractResponse)
def update_payment_status(
    contract_id: UUID,
    status_update: common_schemas.PaymentStatusUpdate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    결제 상태를 변경합니다.
    """
    check_contract_access(db, contract_id, current_profile, require_ownership=True)
    updated_contract = crud.update_payment_status(db, contract_id, status_update)
    return updated_contract

@router.delete("/{contract_id}")
def delete_wholesale_contract(
    contract_id: UUID,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    도매 계약을 삭제합니다.
    """
    check_contract_access(db, contract_id, current_profile, require_ownership=True)
    if not crud.delete_wholesale_contract(db, contract_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="계약 삭제에 실패했습니다"
        )

    return {"message": "계약이 삭제되었습니다"}

@router.delete("/{contract_id}/items/{item_id}")
def delete_contract_item(
    contract_id: UUID,
    item_id: UUID,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    계약의 특정 아이템을 삭제합니다.
    """
    check_contract_access(db, contract_id, current_profile, require_ownership=True)
    if not crud.delete_contract_item(db, contract_id, item_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="아이템 삭제에 실패했습니다"
        )
    
    return {"message": "아이템이 삭제되었습니다"} 