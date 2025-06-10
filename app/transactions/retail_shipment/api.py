from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.auth.utils import get_current_user
from app.database.session import get_db
from . import crud, schemas

router = APIRouter(prefix="/retail-shipments", tags=["retail-shipments"])

@router.post("/", response_model=schemas.RetailShipment)
def create_shipment(
    shipment: schemas.RetailShipmentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    return schemas.RetailShipment.model_validate(crud.create_shipment(db, shipment, company_id))

@router.get("/", response_model=List[schemas.RetailShipment])
def get_shipments(
    contract_id: Optional[UUID] = None,
    retailer_id: Optional[UUID] = None,
    center_id: Optional[UUID] = None,
    wholesaler_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    return [schemas.RetailShipment.model_validate(s) for s in crud.get_shipments(
        db,
        company_id,
        contract_id=contract_id,
        retailer_id=retailer_id,
        center_id=center_id,
        wholesaler_id=wholesaler_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )]

@router.get("/{shipment_id}", response_model=schemas.RetailShipment)
def get_shipment(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    shipment = crud.get_shipment(db, shipment_id, company_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return schemas.RetailShipment.model_validate(shipment)

@router.put("/{shipment_id}", response_model=schemas.RetailShipment)
def update_shipment(
    shipment_id: UUID,
    shipment_update: schemas.RetailShipmentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    shipment = crud.update_shipment(db, shipment_id, company_id, shipment_update)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found or cannot be updated")
    return schemas.RetailShipment.model_validate(shipment)

@router.delete("/{shipment_id}")
def delete_shipment(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    if not crud.delete_shipment(db, shipment_id, company_id):
        raise HTTPException(status_code=404, detail="Shipment not found or cannot be deleted")
    return {"message": "Shipment deleted successfully"}

@router.get("/{shipment_id}/items", response_model=List[schemas.RetailShipmentItem])
def get_shipment_items(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    return [schemas.RetailShipmentItem.model_validate(item) for item in crud.get_shipment_items(db, shipment_id, company_id)]

@router.post("/{shipment_id}/items", response_model=schemas.RetailShipmentItem)
def add_shipment_item(
    shipment_id: UUID,
    item: schemas.RetailShipmentItemCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    db_item = crud.add_shipment_item(db, shipment_id, company_id, item)
    if not db_item:
        raise HTTPException(status_code=404, detail="Shipment not found or cannot be modified")
    return schemas.RetailShipmentItem.model_validate(db_item)

@router.put("/items/{item_id}", response_model=schemas.RetailShipmentItem)
def update_shipment_item(
    item_id: UUID,
    item_update: schemas.RetailShipmentItemUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    item = crud.update_shipment_item(db, item_id, company_id, item_update)
    if not item:
        raise HTTPException(status_code=404, detail="Shipment item not found or cannot be updated")
    return schemas.RetailShipmentItem.model_validate(item)

@router.delete("/items/{item_id}")
def delete_shipment_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    if not crud.delete_shipment_item(db, item_id, company_id):
        raise HTTPException(status_code=404, detail="Shipment item not found or cannot be deleted")
    return {"message": "Shipment item deleted successfully"}

@router.post("/from-contract/{contract_id}", response_model=schemas.RetailShipment)
def create_shipment_from_contract(
    contract_id: UUID,
    shipment: schemas.RetailShipmentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    shipment.contract_id = contract_id
    return schemas.RetailShipment.model_validate(crud.create_shipment(db, shipment, company_id))

@router.get("/contracts/{contract_id}/shipments", response_model=List[schemas.RetailShipment])
def get_contract_shipments(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    return [schemas.RetailShipment.model_validate(s) for s in crud.get_shipments(db, company_id, contract_id=contract_id)]

@router.get("/contracts/{contract_id}/shipment-progress", response_model=List[schemas.ShipmentProgress])
def get_contract_shipment_progress(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    return [schemas.ShipmentProgress.model_validate(p) for p in crud.get_shipment_progress(db, contract_id, company_id)]

@router.get("/retailers/{retailer_id}/shipments", response_model=List[schemas.RetailShipment])
def get_retailer_shipments(
    retailer_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    return [schemas.RetailShipment.model_validate(s) for s in crud.get_shipments(db, company_id, retailer_id=retailer_id)]

@router.get("/my-company/shipments", response_model=List[schemas.RetailShipment])
def get_company_shipments(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    return [schemas.RetailShipment.model_validate(s) for s in crud.get_shipments(db, company_id)]

@router.post("/{shipment_id}/finalize", response_model=schemas.RetailShipment)
def finalize_shipment(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    shipment = crud.finalize_shipment(db, shipment_id, company_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found or cannot be finalized")
    return schemas.RetailShipment.model_validate(shipment) 