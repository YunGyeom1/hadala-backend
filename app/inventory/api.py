from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.auth.utils import get_current_user
from app.database.session import get_db
from app.inventory import crud, schemas
from app.user.models import User

router = APIRouter()

@router.post("/snapshots", response_model=schemas.Inventory)
def create_inventory_snapshot(
    inventory: schemas.InventoryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    return crud.create_inventory(db, inventory, company_id)

@router.get("/snapshots", response_model=List[schemas.Inventory])
def get_inventory_snapshots(
    center_id: Optional[UUID] = None,
    date: Optional[date] = None,
    crop_name: Optional[str] = None,
    quality_grade: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    filters = schemas.InventoryFilter(
        center_id=center_id,
        date=date,
        crop_name=crop_name,
        quality_grade=quality_grade
    )
    return crud.get_inventories(db, company_id, filters, skip, limit)

@router.get("/snapshots/{snapshot_id}", response_model=schemas.Inventory)
def get_inventory_snapshot(
    snapshot_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    inventory = crud.get_inventory(db, snapshot_id, company_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory snapshot not found")
    return inventory

@router.get("/snapshots/{snapshot_id}/items", response_model=List[schemas.InventoryItem])
def get_inventory_items(
    snapshot_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    return crud.get_inventory_items(db, snapshot_id, company_id)

@router.post("/snapshots/{snapshot_id}/items", response_model=schemas.InventoryItem)
def add_inventory_item(
    snapshot_id: UUID,
    item: schemas.InventoryItemCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    db_item = crud.add_inventory_item(db, snapshot_id, company_id, item)
    if not db_item:
        raise HTTPException(status_code=404, detail="Inventory snapshot not found")
    return db_item

@router.put("/items/{item_id}", response_model=schemas.InventoryItem)
def update_inventory_item(
    item_id: UUID,
    item_update: schemas.InventoryItemUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    item = crud.update_inventory_item(db, item_id, company_id, item_update)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item

@router.delete("/items/{item_id}")
def delete_inventory_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    if not crud.delete_inventory_item(db, item_id, company_id):
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return {"message": "Inventory item deleted successfully"}

@router.get("/my-company/inventories", response_model=List[schemas.Inventory])
def get_company_inventories(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    return crud.get_inventories(db, company_id)

@router.get("/my-company/inventories/{date}", response_model=List[schemas.Inventory])
def get_company_inventories_by_date(
    date: date,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company_id = current_user.wholesaler.company_id
    return crud.get_company_inventories_by_date(db, company_id, date)

@router.post("/settlements/today", response_model=schemas.DailySettlement)
def create_today_settlement(
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """오늘자 결산을 생성합니다."""
    settlement = crud.create_today_settlement(db, current_user.company_id)
    if not settlement:
        raise HTTPException(
            status_code=404,
            detail="최근 인벤토리 정보를 찾을 수 없습니다."
        )
    return settlement

@router.post("/settlements/today/center/{center_id}", response_model=schemas.DailySettlement)
def create_today_settlement_for_center(
    center_id: UUID,
    db: Session = Depends(get_db),
    current_user  = Depends(get_current_user)
):
    """특정 센터의 오늘자 결산을 생성합니다."""
    settlement = crud.create_today_settlement(db, current_user.company_id, center_id)
    if not settlement:
        raise HTTPException(
            status_code=404,
            detail="최근 인벤토리 정보를 찾을 수 없습니다."
        )
    return settlement 