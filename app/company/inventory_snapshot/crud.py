from datetime import date
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date, and_
from app.company.inventory_snapshot.schemas import (
    DailyInventorySnapshot, CenterInventorySnapshot, InventorySnapshotItem,
    UpdateDailyInventorySnapshotRequest, UpdateInventorySnapshotItemRequest
)
from app.company.inventory_snapshot.models import CenterInventorySnapshot as CenterInventorySnapshotModel
from app.company.inventory_snapshot.models import CenterInvenrSnapshotItem as CenterInventorySnapshotItemModel
from app.transactions.shipment.models import shipment, shipmentItem
from app.transactions.shipment.models import shipment, shipmentItem
from uuid import UUID

def get_daily_company_inventory_snapshot(
    db: Session,
    target_date: date,
    company_id: UUID
) -> DailyInventorySnapshot:
    # 해당 날짜의 모든 센터 스냅샷 조회
    center_snapshots = db.query(CenterInventorySnapshotModel).filter(
        CenterInventorySnapshotModel.snapshot_date == target_date,
        CenterInventorySnapshotModel.company_id == company_id
    ).all()

    # 센터별 아이템 조회
    center_snapshot_dict = {}
    for snapshot in center_snapshots:
        items = db.query(CenterInventorySnapshotItemModel).filter(
            CenterInventorySnapshotItemModel.center_inventory_snapshot_id == snapshot.id
        ).all()

        # 아이템 정보 변환
        snapshot_items = [
            InventorySnapshotItem(
                product_name=item.product_name,
                quality=item.quality,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price
            ) for item in items
        ]

        # 센터 정보 변환
        center_snapshot_dict[snapshot.center_id] = CenterInventorySnapshot(
            center_id=snapshot.center_id,
            center_name=snapshot.center.name,  # relationship을 통해 center 정보 접근
            total_quantity=snapshot.total_quantity,
            total_price=snapshot.total_price,
            items=snapshot_items
        )

    return DailyInventorySnapshot(
        snapshot_date=target_date,
        centers=list(center_snapshot_dict.values())
    )

def get_daily_company_inventory_snapshots_by_date_range(
    db: Session,
    start_date: date,
    end_date: date,
    company_id: UUID
) -> List[DailyInventorySnapshot]:
    snapshots = []
    current_date = start_date
    
    while current_date <= end_date:
        snapshot = get_daily_inventory_snapshot(db, current_date, company_id)
        snapshots.append(snapshot)
        current_date = current_date.replace(day=current_date.day + 1)
    
    return snapshots

def get_daily_center_inventory_snapshot(
    db: Session,
    target_date: date,
    company_id: UUID,
    center_id: UUID
) -> CenterInventorySnapshot:
    snapshot = db.query(CenterInventorySnapshotModel).filter(
        CenterInventorySnapshotModel.snapshot_date == target_date,
        CenterInventorySnapshotModel.company_id == company_id,
        CenterInventorySnapshotModel.center_id == center_id
    ).first()

    return CenterInventorySnapshot(
        center_id=snapshot.center_id,
        center_name=snapshot.center.name,
        total_quantity=snapshot.total_quantity,
        total_price=snapshot.total_price,
        items=snapshot.items
    )

def create_daily_center_inventory_snapshot(
    db: Session,
    target_date: date,
    company_id: UUID,
    center_id: UUID
) -> CenterInventorySnapshot:
    """
    전날 데이터와 오늘 출하 데이터를 합산하여 오늘의 스냅샷을 생성합니다.
    오늘 스냅샷이 이미 있으면 업데이트하고, 전날 데이터가 없으면 오늘 출하 데이터만으로 생성합니다.
    """
    # 오늘 스냅샷 조회
    existing_snapshot = db.query(CenterInventorySnapshotModel).filter(
        and_(
            CenterInventorySnapshotModel.snapshot_date == target_date,
            CenterInventorySnapshotModel.company_id == company_id,
            CenterInventorySnapshotModel.center_id == center_id
        )
    ).first()
    
    # 출하 데이터 조회
    # 도매 출하 데이터 조회
    wholesale_items = db.query(
        shipmentItem.product_name,
        shipmentItem.quality,
        func.sum(shipmentItem.quantity).label('total_quantity'),
        func.avg(shipmentItem.unit_price).label('avg_unit_price')
    ).join(
        shipment,
        shipmentItem.shipment_id == shipment.id
    ).filter(
        and_(
            shipment.shipment_date == target_date,
            shipment.supplier_company_id == company_id,
            shipment.departure_center_id == center_id
        )
    ).group_by(
        shipmentItem.product_name,
        shipmentItem.quality
    ).all()
    
    # 소매 출하 데이터 조회
    retail_items = db.query(
        shipmentItem.product_name,
        shipmentItem.quality,
        func.sum(shipmentItem.quantity).label('total_quantity'),
        func.avg(shipmentItem.unit_price).label('avg_unit_price')
    ).join(
        shipment,
        shipmentItem.shipment_id == shipment.id
    ).filter(
        and_(
            shipment.shipment_date == target_date,
            shipment.supplier_company_id == company_id,
            shipment.departure_center_id == center_id
        )
    ).group_by(
        shipmentItem.product_name,
        shipmentItem.quality
    ).all()
    
    # 출하 데이터를 딕셔너리로 변환
    shipment_items = {}
    
    # 도매 출하 데이터 처리
    for item in wholesale_items:
        key = (item.product_name, item.quality)
        if key not in shipment_items:
            shipment_items[key] = {
                'quantity': 0,
                'unit_price': 0,
                'total_price': 0
            }
        shipment_items[key]['quantity'] += item.total_quantity
        shipment_items[key]['unit_price'] = item.avg_unit_price
        shipment_items[key]['total_price'] += item.total_quantity * item.avg_unit_price
    
    # 소매 출하 데이터 처리
    for item in retail_items:
        key = (item.product_name, item.quality)
        if key not in shipment_items:
            shipment_items[key] = {
                'quantity': 0,
                'unit_price': 0,
                'total_price': 0
            }
        shipment_items[key]['quantity'] -= item.total_quantity  # 소매는 감소
        shipment_items[key]['unit_price'] = item.avg_unit_price
        shipment_items[key]['total_price'] -= item.total_quantity * item.avg_unit_price
    
    # 전날 스냅샷 조회
    previous_date = target_date.replace(day=target_date.day - 1)
    previous_snapshot = get_daily_center_inventory_snapshot(db, previous_date, company_id, center_id)
    
    # 스냅샷 생성 또는 업데이트
    if existing_snapshot:
        # 기존 스냅샷 업데이트
        center_snapshot = existing_snapshot
    else:
        # 새로운 스냅샷 생성
        center_snapshot = CenterInventorySnapshotModel(
            snapshot_date=target_date,
            company_id=company_id,
            center_id=center_id,
            total_quantity=0,
            total_price=0,
            finalized=False
        )
        db.add(center_snapshot)
        db.flush()
    
    # 아이템 생성 및 합산
    new_items = []
    total_quantity = 0
    total_price = 0
    
    if previous_snapshot:
        # 전날 아이템 복사 및 출하 데이터 합산
        for item in previous_snapshot.items:
            key = (item.product_name, item.quality)
            shipment_data = shipment_items.get(key, {'quantity': 0, 'unit_price': item.unit_price, 'total_price': 0})
            
            new_quantity = item.quantity + shipment_data['quantity']
            new_unit_price = shipment_data['unit_price'] if shipment_data['quantity'] != 0 else item.unit_price
            new_total_price = new_quantity * new_unit_price
            
            new_item = CenterInventorySnapshotItemModel(
                center_inventory_snapshot_id=center_snapshot.id,
                product_name=item.product_name,
                quantity=new_quantity,
                quality=item.quality,
                unit_price=new_unit_price,
                total_price=new_total_price
            )
            db.add(new_item)
            
            new_items.append(
                InventorySnapshotItem(
                    product_name=item.product_name,
                    quantity=new_quantity,
                    quality=item.quality,
                    unit_price=new_unit_price,
                    total_price=new_total_price
                )
            )
            
            total_quantity += new_quantity
            total_price += new_total_price
    
    # 새로운 출하 아이템 추가 (전날에 없던 아이템)
    for (product_name, quality), shipment_data in shipment_items.items():
        if not previous_snapshot or not any(
            item.product_name == product_name and item.quality == quality 
            for item in previous_snapshot.items
        ):
            new_quantity = shipment_data['quantity']
            new_unit_price = shipment_data['unit_price']
            new_total_price = new_quantity * new_unit_price
            
            new_item = CenterInventorySnapshotItemModel(
                center_inventory_snapshot_id=center_snapshot.id,
                product_name=product_name,
                quantity=new_quantity,
                quality=quality,
                unit_price=new_unit_price,
                total_price=new_total_price
            )
            db.add(new_item)
            
            new_items.append(
                InventorySnapshotItem(
                    product_name=product_name,
                    quantity=new_quantity,
                    quality=quality,
                    unit_price=new_unit_price,
                    total_price=new_total_price
                )
            )
            
            total_quantity += new_quantity
            total_price += new_total_price
    
    # 센터 스냅샷 업데이트
    center_snapshot.total_quantity = total_quantity
    center_snapshot.total_price = total_price
    
    db.commit()
    
    return CenterInventorySnapshot(
        center_id=center_id,
        center_name=center_snapshot.center.name,
        total_quantity=total_quantity,
        total_price=total_price,
        items=new_items
    )

def update_daily_inventory_snapshot(
    db: Session,
    update_request: UpdateDailyInventorySnapshotRequest,
    company_id: UUID,
    profile_id: UUID
) -> Tuple[DailyInventorySnapshot, List[shipment], List[shipment]]:
    """
    일자별 인벤토리 스냅샷을 수정하고, 필요한 도매/소매 출하 데이터를 생성합니다.
    """
    # 1. 현재 스냅샷 조회
    current_snapshot = get_daily_company_inventory_snapshot(db, update_request.snapshot_date, company_id)
    if not current_snapshot.centers:
        raise ValueError("해당 날짜의 스냅샷이 존재하지 않습니다.")
    
    created_shipments = []
    created_shipments = []
    
    # 2. 각 센터별 업데이트 처리
    for center_update in update_request.centers:
        # 2.1 현재 센터 스냅샷 조회
        db_snapshot = db.query(CenterInventorySnapshotModel).filter(
            and_(
                CenterInventorySnapshotModel.snapshot_date == update_request.snapshot_date,
                CenterInventorySnapshotModel.center_id == center_update.center_id,
                CenterInventorySnapshotModel.company_id == company_id
            )
        ).first()
        
        if not db_snapshot:
            continue
            
        # 2.2 아이템별 수량 차이 계산 및 출하 데이터 생성
        wholesale_items = []
        retail_items = []
        total_wholesale_price = 0
        total_retail_price = 0
        
        for item_update in center_update.items:
            db_item = db.query(CenterInventorySnapshotItemModel).filter(
                and_(
                    CenterInventorySnapshotItemModel.center_inventory_snapshot_id == db_snapshot.id,
                    CenterInventorySnapshotItemModel.product_name == item_update.product_name,
                    CenterInventorySnapshotItemModel.quality == item_update.quality
                )
            ).first()
            
            if not db_item:
                continue
                
            quantity_diff = item_update.quantity - db_item.quantity
            
            if quantity_diff > 0:  # 도매 출하
                wholesale_items.append({
                    'product_name': item_update.product_name,
                    'quantity': quantity_diff,
                    'quality': item_update.quality,
                    'unit_price': item_update.unit_price,
                    'total_price': quantity_diff * item_update.unit_price
                })
                total_wholesale_price += quantity_diff * item_update.unit_price
            elif quantity_diff < 0:  # 소매 출하
                retail_items.append({
                    'product_name': item_update.product_name,
                    'quantity': abs(quantity_diff),
                    'quality': item_update.quality,
                    'unit_price': item_update.unit_price,
                    'total_price': abs(quantity_diff) * item_update.unit_price
                })
                total_retail_price += abs(quantity_diff) * item_update.unit_price
            
            # 아이템 업데이트
            db_item.quantity = item_update.quantity
            db_item.unit_price = item_update.unit_price
            db_item.total_price = item_update.quantity * item_update.unit_price
        
        # 2.3 도매 출하 데이터 생성
        if wholesale_items:
            shipment = shipment(
                title=f"인벤토리 조정 - {center_update.center_id}",
                creator_id=profile_id,
                supplier_company_id=company_id,
                departure_center_id=center_update.center_id,
                total_price=total_wholesale_price,
                status="completed",
                shipment_date=update_request.snapshot_date
            )
            db.add(shipment)
            db.flush()
            
            for item in wholesale_items:
                shipment_item = shipmentItem(
                    shipment_id=shipment.id,
                    product_name=item['product_name'],
                    quantity=item['quantity'],
                    quality=item['quality'],
                    unit_price=item['unit_price'],
                    total_price=item['total_price']
                )
                db.add(shipment_item)
            
            created_shipments.append(shipment)
        
        # 2.4 소매 출하 데이터 생성
        if retail_items:
            shipment = shipment(
                title=f"인벤토리 조정 - {center_update.center_id}",
                creator_id=profile_id,
                supplier_company_id=company_id,
                departure_center_id=center_update.center_id,
                total_price=total_retail_price,
                status="completed",
                shipment_date=update_request.snapshot_date
            )
            db.add(shipment)
            db.flush()
            
            for item in retail_items:
                shipment_item = shipmentItem(
                    shipment_id=shipment.id,
                    product_name=item['product_name'],
                    quantity=item['quantity'],
                    quality=item['quality'],
                    unit_price=item['unit_price'],
                    total_price=item['total_price']
                )
                db.add(shipment_item)
            
            created_shipments.append(shipment)
        
        # 2.5 센터 스냅샷 업데이트
        db_snapshot.total_quantity = sum(item.quantity for item in center_update.items)
        db_snapshot.total_price = sum(item.quantity * item.unit_price for item in center_update.items)
    
    # 3. 이후 날짜의 스냅샷들 업데이트
    next_date = update_request.snapshot_date
    while True:
        # 다음 날짜의 스냅샷 생성 또는 조회
        next_snapshot = create_daily_center_inventory_snapshot(db, next_date, company_id, center_update.center_id)
        if not next_snapshot:  # 더 이상 스냅샷이 없으면 종료
            break
            
        next_date = next_date.replace(day=next_date.day + 1)
    
    db.commit()
    
    # 업데이트된 스냅샷 반환
    updated_snapshot = get_daily_company_inventory_snapshot(db, update_request.snapshot_date, company_id)
    return updated_snapshot, created_shipments, created_shipments
