from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.auth.utils import get_current_user, verify_company_affiliation
from app.database.session import get_db
from . import crud, schemas
from .models import ContractStatus, PaymentStatus

router = APIRouter()

@router.post("/", response_model=schemas.RetailContract)
def create_contract(
    contract: schemas.RetailContractCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = verify_company_affiliation(current_user)
    return crud.create_contract(db, contract, company_id)

@router.get("/", response_model=List[schemas.RetailContract])
def get_contracts(
    status: Optional[ContractStatus] = None,
    retailer_id: Optional[UUID] = None,
    center_id: Optional[UUID] = None,
    wholesaler_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = verify_company_affiliation(current_user)
    return crud.get_contracts(
        db,
        company_id,
        status=status,
        retailer_id=retailer_id,
        center_id=center_id,
        wholesaler_id=wholesaler_id,
        skip=skip,
        limit=limit
    )

@router.get("/{contract_id}", response_model=schemas.RetailContract)
def get_contract(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = verify_company_affiliation(current_user)
    contract = crud.get_contract(db, contract_id, company_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract

@router.put("/{contract_id}", response_model=schemas.RetailContract)
def update_contract(
    contract_id: UUID,
    contract_update: schemas.RetailContractUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = verify_company_affiliation(current_user)
    contract = crud.update_contract(db, contract_id, company_id, contract_update)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract

@router.delete("/{contract_id}")
def delete_contract(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = verify_company_affiliation(current_user)
    if not crud.delete_contract(db, contract_id, company_id):
        raise HTTPException(status_code=404, detail="Contract not found or cannot be deleted")
    return {"message": "Contract deleted successfully"}

@router.put("/{contract_id}/status", response_model=schemas.RetailContract)
def update_contract_status(
    contract_id: UUID,
    status: ContractStatus,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = verify_company_affiliation(current_user)
    contract = crud.update_contract_status(db, contract_id, company_id, status)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract

@router.put("/{contract_id}/payment-status", response_model=schemas.RetailContract)
def update_payment_status(
    contract_id: UUID,
    payment_status: PaymentStatus,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = verify_company_affiliation(current_user)
    contract = crud.update_payment_status(db, contract_id, company_id, payment_status)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract

@router.get("/{contract_id}/items", response_model=List[schemas.RetailContractItem])
def get_contract_items(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = verify_company_affiliation(current_user)
    return crud.get_contract_items(db, contract_id, company_id)

@router.put("/items/{item_id}", response_model=schemas.RetailContractItem)
def update_contract_item(
    item_id: UUID,
    item_update: schemas.RetailContractItemUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = verify_company_affiliation(current_user)
    item = crud.update_contract_item(db, item_id, company_id, item_update)
    if not item:
        raise HTTPException(status_code=404, detail="Contract item not found")
    return item

@router.delete("/items/{item_id}")
def delete_contract_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = verify_company_affiliation(current_user)
    if not crud.delete_contract_item(db, item_id, company_id):
        raise HTTPException(status_code=404, detail="Contract item not found")
    return {"message": "Contract item deleted successfully"} 