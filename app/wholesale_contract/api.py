from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.database.session import get_db
from app.core.auth.utils import get_current_user
from app.user.models import User
from . import crud, schemas, models
from .models import ContractStatus, PaymentStatus

router = APIRouter(prefix="/wholesale-contracts", tags=["wholesale-contracts"])  

@router.post("/", response_model=schemas.WholesaleContract)
def create_contract(
    contract: schemas.WholesaleContractCreate,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """새 계약 생성"""
    company_id = current_user.wholesaler.company_id
    return schemas.WholesaleContract.model_validate(crud.create_contract(db, contract))

@router.get("/", response_model=List[schemas.WholesaleContract])
def get_contracts(
    status: Optional[ContractStatus] = None,
    farmer_id: Optional[UUID] = None,
    center_id: Optional[UUID] = None,
    wholesaler_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """계약 목록 조회"""
    company_id = current_user.wholesaler.company_id
    return [schemas.WholesaleContract.model_validate(c) for c in crud.get_contracts(
        db,
        company_id,
        status=status,
        farmer_id=farmer_id,
        center_id=center_id,
        wholesaler_id=wholesaler_id,
        skip=skip,
        limit=limit
    )]

@router.get("/{contract_id}", response_model=schemas.WholesaleContract)
def get_contract(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """특정 계약 조회"""
    contract = crud.get_contract(db, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="계약을 찾을 수 없습니다.")
    return schemas.WholesaleContract.model_validate(contract)

@router.put("/{contract_id}", response_model=schemas.WholesaleContract)
def update_contract(
    contract_id: UUID,
    contract_update: schemas.WholesaleContractUpdate,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """계약 정보를 업데이트합니다."""
    contract = crud.get_contract(db, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.company_id != current_user.wholesaler.company_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this contract")
    if contract_update.payment_status and contract_update.payment_status != contract.payment_status:
        crud.create_payment_log(
            db=db,
            contract_id=contract_id,
            old_status=contract.payment_status,
            new_status=contract_update.payment_status,
            changed_by=current_user.id
        )
    updated_contract = crud.update_contract(db, contract_id, contract_update)
    if not updated_contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return schemas.WholesaleContract.model_validate(updated_contract)

@router.delete("/{contract_id}")
def delete_contract(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """계약 삭제"""
    company_id = current_user.wholesaler.company_id
    if not crud.delete_contract(db, contract_id, company_id):
        raise HTTPException(status_code=404, detail="계약을 찾을 수 없거나 삭제할 수 없는 상태입니다.")
    return {"message": "계약이 삭제되었습니다."}

@router.post("/{contract_id}/confirm", response_model=schemas.WholesaleContract)
def confirm_contract(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """계약 확정"""
    company_id = current_user.wholesaler.company_id
    contract = crud.update_contract_status(db, contract_id, models.ContractStatus.CONFIRMED, company_id)
    if not contract:
        raise HTTPException(status_code=404, detail="계약을 찾을 수 없습니다.")
    return schemas.WholesaleContract.model_validate(contract)

@router.post("/{contract_id}/complete", response_model=schemas.WholesaleContract)
def complete_contract(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """계약 완료"""
    company_id = current_user.wholesaler.company_id
    contract = crud.update_contract_status(db, contract_id, models.ContractStatus.COMPLETED, company_id)
    if not contract:
        raise HTTPException(status_code=404, detail="계약을 찾을 수 없습니다.")
    return schemas.WholesaleContract.model_validate(contract)

@router.post("/{contract_id}/cancel", response_model=schemas.WholesaleContract)
def cancel_contract(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """계약 취소"""
    company_id = current_user.wholesaler.company_id
    contract = crud.update_contract_status(db, contract_id, models.ContractStatus.CANCELLED, company_id)
    if not contract:
        raise HTTPException(status_code=404, detail="계약을 찾을 수 없습니다.")
    return schemas.WholesaleContract.model_validate(contract)

@router.get("/{contract_id}/items", response_model=List[schemas.WholesaleContractItem])
def get_contract_items(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """계약 품목 목록 조회"""
    company_id = current_user.wholesaler.company_id
    items = crud.get_contract_items(db, contract_id)
    if items is None:
        raise HTTPException(status_code=404, detail="계약을 찾을 수 없습니다.")
    return [schemas.WholesaleContractItem.model_validate(item) for item in items]

@router.put("/items/{item_id}", response_model=schemas.WholesaleContractItem)
def update_contract_item(
    item_id: UUID,
    item: schemas.WholesaleContractItemUpdate,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """계약 품목 수정"""
    company_id = current_user.wholesaler.company_id
    updated_item = crud.update_contract_item(db, item_id, item, company_id)
    if not updated_item:
        raise HTTPException(status_code=404, detail="품목을 찾을 수 없거나 수정할 수 없는 상태입니다.")
    return schemas.WholesaleContractItem.model_validate(updated_item)

@router.delete("/items/{item_id}")
def delete_contract_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """계약 품목 삭제"""
    company_id = current_user.wholesaler.company_id
    if not crud.delete_contract_item(db, item_id, company_id):
        raise HTTPException(status_code=404, detail="품목을 찾을 수 없거나 삭제할 수 없는 상태입니다.")
    return {"message": "품목이 삭제되었습니다."}

@router.get("/{contract_id}/payment-logs", response_model=List[schemas.PaymentLog])
def get_contract_payment_logs(
    contract_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """계약의 결제 상태 변경 로그를 조회합니다."""
    company_id = current_user.wholesaler.company_id
    logs = crud.get_contract_payment_logs(db, contract_id, company_id, skip, limit)
    if not logs:
        raise HTTPException(status_code=404, detail="계약을 찾을 수 없습니다.")
    return [schemas.PaymentLog.model_validate(log) for log in logs]

@router.get("/payment-logs/{log_id}", response_model=schemas.PaymentLog)
def get_payment_log(
    log_id: UUID,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """특정 결제 상태 변경 로그를 조회합니다."""
    company_id = current_user.wholesaler.company_id
    log = crud.get_payment_log(db, log_id, company_id)
    if not log:
        raise HTTPException(status_code=404, detail="결제 로그를 찾을 수 없습니다.")
    return schemas.PaymentLog.model_validate(log) 