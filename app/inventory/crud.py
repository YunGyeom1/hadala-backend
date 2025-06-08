from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import date, datetime
from uuid import UUID

from app.inventory.models import CompanyCropInventory, CompanyCropInventoryItem
from app.inventory.schemas import InventoryCreate, InventoryUpdate, InventoryFilter, InventoryItemCreate, InventoryItemUpdate
from app.management.models import DailySettlement
from app.wholesale_shipment.models import WholesaleShipment
from app.retail_shipment.models import RetailShipment

def create_inventory(db: Session, inventory: InventoryCreate, company_id: UUID) -> CompanyCropInventory:
    db_inventory = CompanyCropInventory(
        date=inventory.date,
        company_id=company_id,
        center_id=inventory.center_id
    )
    db.add(db_inventory)
    db.flush()  # ID 생성을 위해 flush

    # 품목 추가
    for item in inventory.items:
        db_item = CompanyCropInventoryItem(
            inventory_id=db_inventory.id,
            crop_name=item.crop_name,
            quality_grade=item.quality_grade,
            quantity=item.quantity
        )
        db.add(db_item)

    db.commit()
    db.refresh(db_inventory)
    return db_inventory

def get_inventories(
    db: Session,
    company_id: UUID,
    filters: Optional[InventoryFilter] = None,
    skip: int = 0,
    limit: int = 100
) -> List[CompanyCropInventory]:
    query = db.query(CompanyCropInventory).filter(CompanyCropInventory.company_id == company_id)

    if filters:
        if filters.center_id:
            query = query.filter(CompanyCropInventory.center_id == filters.center_id)
        if filters.date:
            query = query.filter(CompanyCropInventory.date == filters.date)
        if filters.crop_name or filters.quality_grade:
            query = query.join(CompanyCropInventoryItem)
            if filters.crop_name:
                query = query.filter(CompanyCropInventoryItem.crop_name == filters.crop_name)
            if filters.quality_grade:
                query = query.filter(CompanyCropInventoryItem.quality_grade == filters.quality_grade)

    return query.offset(skip).limit(limit).all()

def get_inventory(db: Session, inventory_id: UUID, company_id: UUID) -> Optional[CompanyCropInventory]:
    return db.query(CompanyCropInventory).filter(
        and_(
            CompanyCropInventory.id == inventory_id,
            CompanyCropInventory.company_id == company_id
        )
    ).first()

def update_inventory(
    db: Session,
    inventory_id: UUID,
    company_id: UUID,
    inventory_update: InventoryUpdate
) -> Optional[CompanyCropInventory]:
    db_inventory = get_inventory(db, inventory_id, company_id)
    if not db_inventory:
        return None

    update_data = inventory_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_inventory, field, value)

    db.commit()
    db.refresh(db_inventory)
    return db_inventory

def delete_inventory(db: Session, inventory_id: UUID, company_id: UUID) -> bool:
    db_inventory = get_inventory(db, inventory_id, company_id)
    if not db_inventory:
        return False

    db.delete(db_inventory)
    db.commit()
    return True

def get_inventory_items(
    db: Session,
    inventory_id: UUID,
    company_id: UUID
) -> List[CompanyCropInventoryItem]:
    return db.query(CompanyCropInventoryItem).join(CompanyCropInventory).filter(
        and_(
            CompanyCropInventoryItem.inventory_id == inventory_id,
            CompanyCropInventory.company_id == company_id
        )
    ).all()

def add_inventory_item(
    db: Session,
    inventory_id: UUID,
    company_id: UUID,
    item: InventoryItemCreate
) -> Optional[CompanyCropInventoryItem]:
    db_inventory = get_inventory(db, inventory_id, company_id)
    if not db_inventory:
        return None

    db_item = CompanyCropInventoryItem(
        inventory_id=inventory_id,
        crop_name=item.crop_name,
        quality_grade=item.quality_grade,
        quantity=item.quantity
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_inventory_item(
    db: Session,
    item_id: UUID,
    company_id: UUID,
    item_update: InventoryItemUpdate
) -> Optional[CompanyCropInventoryItem]:
    db_item = db.query(CompanyCropInventoryItem).join(CompanyCropInventory).filter(
        and_(
            CompanyCropInventoryItem.id == item_id,
            CompanyCropInventory.company_id == company_id
        )
    ).first()

    if not db_item:
        return None

    update_data = item_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)
    return db_item

def delete_inventory_item(db: Session, item_id: UUID, company_id: UUID) -> bool:
    db_item = db.query(CompanyCropInventoryItem).join(CompanyCropInventory).filter(
        and_(
            CompanyCropInventoryItem.id == item_id,
            CompanyCropInventory.company_id == company_id
        )
    ).first()

    if not db_item:
        return False

    db.delete(db_item)
    db.commit()
    return True

def get_company_inventories_by_date(
    db: Session,
    company_id: UUID,
    target_date: date
) -> List[CompanyCropInventory]:
    return db.query(CompanyCropInventory).filter(
        and_(
            CompanyCropInventory.company_id == company_id,
            CompanyCropInventory.date == target_date
        )
    ).all()

def get_latest_inventory_date(db: Session, company_id: UUID) -> Optional[date]:
    """회사의 가장 최근 인벤토리 날짜를 조회합니다."""
    latest_inventory = db.query(CompanyCropInventory)\
        .filter(CompanyCropInventory.company_id == company_id)\
        .order_by(CompanyCropInventory.date.desc())\
        .first()
    return latest_inventory.date if latest_inventory else None


def calculate_daily_settlement_for_date(
    db: Session,
    company_id: UUID,
    center_id: Optional[UUID],
    target_date: date
) -> Optional[DailySettlement]:
    """특정 날짜의 결산 정보를 계산합니다."""
    # 가장 최근 인벤토리 날짜 조회
    latest_inventory_date = get_latest_inventory_date(db, company_id)
    if not latest_inventory_date:
        return None

    # 도매 출하 정보 조회
    shipments = db.query(WholesaleShipment).filter(
        WholesaleShipment.company_id == company_id,
        WholesaleShipment.center_id == center_id,
        WholesaleShipment.shipment_date >= latest_inventory_date,
        WholesaleShipment.shipment_date <= target_date
    ).all()

    # 소매 출하 정보 조회
    retail_shipments = db.query(RetailShipment).filter(
        RetailShipment.company_id == company_id,
        RetailShipment.shipment_date >= latest_inventory_date,
        RetailShipment.shipment_date <= target_date
    ).all()

    # 수량 및 가격 집계
    total_wholesale_in_kg = 0
    total_wholesale_in_price = 0
    for shipment in shipments:
        for item in shipment.items:
            total_wholesale_in_kg += item.quantity_kg
            total_wholesale_in_price += item.quantity_kg * item.unit_price

    total_retail_out_kg = 0
    total_retail_out_price = 0
    for shipment in retail_shipments:
        for item in shipment.items:
            total_retail_out_kg += item.quantity_kg
            total_retail_out_price += item.quantity_kg * item.unit_price

    # 계약 대비 차이 계산
    discrepancy_in_kg = 0
    discrepancy_out_kg = 0

    for shipment in shipments:
        contract = shipment.contract
        if contract:
            contract_quantity = sum(item.quantity_kg for item in contract.items)
            shipment_quantity = sum(item.quantity_kg for item in shipment.items)
            discrepancy_in_kg += shipment_quantity - contract_quantity

    for shipment in retail_shipments:
        contract = shipment.contract
        if contract:
            contract_quantity = sum(item.quantity_kg for item in contract.items)
            shipment_quantity = sum(item.quantity_kg for item in shipment.items)
            discrepancy_out_kg += shipment_quantity - contract_quantity

    # 결산 정보 생성
    settlement = DailySettlement(
        date=target_date,
        company_id=company_id,
        center_id=center_id,
        total_wholesale_in_kg=total_wholesale_in_kg,
        total_wholesale_in_price=total_wholesale_in_price,
        total_retail_out_kg=total_retail_out_kg,
        total_retail_out_price=total_retail_out_price,
        discrepancy_in_kg=discrepancy_in_kg,
        discrepancy_out_kg=discrepancy_out_kg,
        total_in_kg=total_wholesale_in_kg,
        total_out_kg=total_retail_out_kg
    )

    db.add(settlement)
    db.commit()
    db.refresh(settlement)
    return settlement
def create_today_settlement(
    db: Session,
    company_id: UUID,
    center_id: Optional[UUID] = None
) -> Optional[DailySettlement]:
    """오늘자 결산을 생성합니다."""
    today = date.today()
    return calculate_daily_settlement_for_date(db, company_id, center_id, today) 