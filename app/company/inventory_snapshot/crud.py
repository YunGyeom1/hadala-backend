from datetime import date, timedelta
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date, and_, or_
from app.company.inventory_snapshot.schemas import (
    DailyInventorySnapshot, CenterInventorySnapshot, InventorySnapshotItem,
    UpdateDailyInventorySnapshotRequest, InitialCenterInventoryRequest
)
from app.company.inventory_snapshot.models import CenterInventorySnapshot as CenterInventorySnapshotModel
from app.company.inventory_snapshot.models import CenterInventorySnapshotItem as CenterInventorySnapshotItemModel
from app.transactions.shipment.models import Shipment, ShipmentItem
from app.company.center.models import Center
from uuid import UUID
import uuid

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

    # 스냅샷이 없으면 자동으로 생성
    if not center_snapshots:
        # 회사의 모든 센터 조회
        centers = db.query(Center).filter(Center.company_id == company_id).all()
        
        # 각 센터에 대해 스냅샷 생성
        for center in centers:
            create_daily_center_inventory_snapshot(db, target_date, company_id, center.id, None)
        
        # 다시 조회
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
        snapshot = get_daily_company_inventory_snapshot(db, current_date, company_id)
        snapshots.append(snapshot)
        current_date = current_date.replace(day=current_date.day + 1)
    
    return snapshots

def get_daily_center_inventory_snapshot(
    db: Session,
    target_date: date,
    company_id: UUID,
    center_id: UUID
) -> Optional[CenterInventorySnapshot]:
    snapshot = db.query(CenterInventorySnapshotModel).filter(
        CenterInventorySnapshotModel.snapshot_date == target_date,
        CenterInventorySnapshotModel.company_id == company_id,
        CenterInventorySnapshotModel.center_id == center_id
    ).first()
    if not snapshot:
        return create_daily_center_inventory_snapshot(db, target_date, company_id, center_id)

    # 아이템 변환
    items = db.query(CenterInventorySnapshotItemModel).filter(
        CenterInventorySnapshotItemModel.center_inventory_snapshot_id == snapshot.id
    ).all()
    snapshot_items = [
        InventorySnapshotItem(
            product_name=item.product_name,
            quality=item.quality,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.total_price
        ) for item in items
    ]

    return CenterInventorySnapshot(
        center_id=snapshot.center_id,
        center_name=snapshot.center.name,
        total_quantity=snapshot.total_quantity,
        total_price=snapshot.total_price,
        items=snapshot_items
    )

def create_daily_center_inventory_snapshot(
    db: Session,
    target_date: date,
    company_id: UUID,
    center_id: UUID,
    creator_id: UUID = None,
    contract_id: UUID = None
) -> CenterInventorySnapshot:
    """
    가장 최근 finalized된 스냅샷부터 매일 생성하거나, finalized가 없으면 가장 오래된 shipment부터 매일 생성합니다.
    shipment가 없으면 기본 스냅샷을 생성합니다.
    """
    print(f"=== create_daily_center_inventory_snapshot 호출: center_id={center_id}, target_date={target_date} ===")
    
    # 가장 최근 finalized된 스냅샷 조회
    latest_finalized_snapshot = db.query(CenterInventorySnapshotModel).filter(
        and_(
            CenterInventorySnapshotModel.center_id == center_id,
            CenterInventorySnapshotModel.company_id == company_id,
            CenterInventorySnapshotModel.finalized == True
        )
    ).order_by(CenterInventorySnapshotModel.snapshot_date.desc()).first()
    
    print(f"최근 finalized 스냅샷: {latest_finalized_snapshot.snapshot_date if latest_finalized_snapshot else 'None'}")
    
    if latest_finalized_snapshot:
        # finalized된 스냅샷이 있으면 그 이후부터 매일 생성
        start_date = latest_finalized_snapshot.snapshot_date + timedelta(days=1)
        print(f"finalized 스냅샷 이후부터 생성: {start_date} ~ {target_date}")
        create_daily_snapshots_from_finalized(db, start_date, target_date, company_id, center_id)
        
        # target_date의 스냅샷 조회
        target_snapshot = db.query(CenterInventorySnapshotModel).filter(
            and_(
                CenterInventorySnapshotModel.snapshot_date == target_date,
                CenterInventorySnapshotModel.center_id == center_id,
                CenterInventorySnapshotModel.company_id == company_id
            )
        ).first()
        
        print(f"target_date 스냅샷 조회 결과: {target_snapshot is not None}")
        
        if target_snapshot:
            # 아이템 변환
            items = db.query(CenterInventorySnapshotItemModel).filter(
                CenterInventorySnapshotItemModel.center_inventory_snapshot_id == target_snapshot.id
            ).all()
            snapshot_items = [
                InventorySnapshotItem(
                    product_name=item.product_name,
                    quality=item.quality,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price
                ) for item in items
            ]
            
            return CenterInventorySnapshot(
                center_id=center_id,
                center_name=target_snapshot.center.name,
                total_quantity=target_snapshot.total_quantity,
                total_price=target_snapshot.total_price,
                items=snapshot_items
            )
    else:
        # finalized된 스냅샷이 없으면 가장 오래된 shipment부터 매일 생성
        print("finalized 스냅샷이 없어서 shipment부터 생성")
        oldest_shipment = db.query(Shipment).filter(
            and_(
                or_(
                    Shipment.supplier_company_id == company_id,
                    Shipment.receiver_company_id == company_id
                ),
                or_(
                    Shipment.departure_center_id == center_id,
                    Shipment.arrival_center_id == center_id
                )
            )
        ).order_by(Shipment.shipment_datetime.asc()).first()
        
        print(f"가장 오래된 shipment: {oldest_shipment.shipment_datetime if oldest_shipment else 'None'}")
        
        if oldest_shipment:
            start_date = oldest_shipment.shipment_datetime.date()
            print(f"shipment부터 생성: {start_date} ~ {target_date}")
            create_daily_snapshots_from_shipments(db, start_date, target_date, company_id, center_id)
            
            # target_date의 스냅샷 조회
            target_snapshot = db.query(CenterInventorySnapshotModel).filter(
                and_(
                    CenterInventorySnapshotModel.snapshot_date == target_date,
                    CenterInventorySnapshotModel.center_id == center_id,
                    CenterInventorySnapshotModel.company_id == company_id
                )
            ).first()
            
            print(f"target_date 스냅샷 조회 결과: {target_snapshot is not None}")
            
            if target_snapshot:
                # 아이템 변환
                items = db.query(CenterInventorySnapshotItemModel).filter(
                    CenterInventorySnapshotItemModel.center_inventory_snapshot_id == target_snapshot.id
                ).all()
                snapshot_items = [
                    InventorySnapshotItem(
                        product_name=item.product_name,
                        quality=item.quality,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        total_price=item.total_price
                    ) for item in items
                ]
                
                return CenterInventorySnapshot(
                    center_id=center_id,
                    center_name=target_snapshot.center.name,
                    total_quantity=target_snapshot.total_quantity,
                    total_price=target_snapshot.total_price,
                    items=snapshot_items
                )
        else:
            # shipment가 없으면 기본 스냅샷 생성
            print("shipment가 없어서 기본 스냅샷 생성")
            center = db.query(Center).filter(Center.id == center_id).first()
            if not center:
                print("센터를 찾을 수 없음")
                return None
            
            # 해당 날짜의 스냅샷이 이미 있는지 확인
            existing_snapshot = db.query(CenterInventorySnapshotModel).filter(
                and_(
                    CenterInventorySnapshotModel.snapshot_date == target_date,
                    CenterInventorySnapshotModel.center_id == center_id,
                    CenterInventorySnapshotModel.company_id == company_id
                )
            ).first()
            
            if not existing_snapshot:
                # 새로운 기본 스냅샷 생성
                center_snapshot = CenterInventorySnapshotModel(
                    snapshot_date=target_date,
                    company_id=company_id,
                    center_id=center_id,
                    total_quantity=0,
                    total_price=0,
                    finalized=False
                )
                db.add(center_snapshot)
                db.commit()
                db.refresh(center_snapshot)
                print(f"기본 스냅샷 생성 완료: {center_snapshot.id}")
                
                return CenterInventorySnapshot(
                    center_id=center_id,
                    center_name=center.name,
                    total_quantity=0,
                    total_price=0,
                    items=[]
                )
            else:
                # 기존 스냅샷 반환
                items = db.query(CenterInventorySnapshotItemModel).filter(
                    CenterInventorySnapshotItemModel.center_inventory_snapshot_id == existing_snapshot.id
                ).all()
                snapshot_items = [
                    InventorySnapshotItem(
                        product_name=item.product_name,
                        quality=item.quality,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        total_price=item.total_price
                    ) for item in items
                ]
                
                return CenterInventorySnapshot(
                    center_id=center_id,
                    center_name=existing_snapshot.center.name,
                    total_quantity=existing_snapshot.total_quantity,
                    total_price=existing_snapshot.total_price,
                    items=snapshot_items
                )
    
    print("스냅샷 생성 실패 - None 반환")
    return None

def create_daily_snapshots_from_shipments(
    db: Session,
    start_date: date,
    end_date: date,
    company_id: UUID,
    center_id: UUID
):
    """
    가장 오래된 shipment부터 매일치 스냅샷을 생성합니다.
    """
    current_date = start_date
    
    while current_date <= end_date:
        # 해당 날짜의 스냅샷이 이미 있는지 확인
        existing_snapshot = db.query(CenterInventorySnapshotModel).filter(
            and_(
                CenterInventorySnapshotModel.snapshot_date == current_date,
                CenterInventorySnapshotModel.center_id == center_id,
                CenterInventorySnapshotModel.company_id == company_id
            )
        ).first()
        
        if not existing_snapshot:
            # 새로운 스냅샷 생성 (not finalized)
            center_snapshot = CenterInventorySnapshotModel(
                snapshot_date=current_date,
                company_id=company_id,
                center_id=center_id,
                total_quantity=0,
                total_price=0,
                finalized=False
            )
            db.add(center_snapshot)
            db.flush()
            
            # 전날 스냅샷 조회하여 아이템 복사
            previous_date = current_date - timedelta(days=1)
            previous_snapshot = db.query(CenterInventorySnapshotModel).filter(
                and_(
                    CenterInventorySnapshotModel.snapshot_date == previous_date,
                    CenterInventorySnapshotModel.center_id == center_id,
                    CenterInventorySnapshotModel.company_id == company_id
                )
            ).first()
            
            if previous_snapshot:
                # 전날 아이템 복사
                for item in previous_snapshot.items:
                    new_item = CenterInventorySnapshotItemModel(
                        id=uuid.uuid4(),
                        center_inventory_snapshot_id=center_snapshot.id,
                        product_name=item.product_name,
                        quantity=item.quantity,
                        quality=item.quality,
                        unit_price=item.unit_price,
                        total_price=item.total_price
                    )
                    db.add(new_item)
                db.flush()  # 복사 후 반드시 flush!
            
            # 출하(−) / 입하(+) 데이터 일괄 적용
            shipment_specs = [
                {  # 출하(감소)
                    'multiplier': -1,
                    'center_field': Shipment.departure_center_id,
                    'company_field': Shipment.supplier_company_id,
                },
                {  # 입하(증가)
                    'multiplier': 1,
                    'center_field': Shipment.arrival_center_id,
                    'company_field': Shipment.receiver_company_id,
                }
            ]

            for spec in shipment_specs:
                query = db.query(
                    ShipmentItem.product_name,
                    ShipmentItem.quality,
                    func.sum(ShipmentItem.quantity).label('total_quantity'),
                    func.avg(ShipmentItem.unit_price).label('avg_unit_price')
                ).join(Shipment, ShipmentItem.shipment_id == Shipment.id).filter(
                    and_(
                        cast(Shipment.shipment_datetime, Date) == current_date,
                        spec['company_field'] == company_id,
                        spec['center_field'] == center_id
                    )
                ).group_by(
                    ShipmentItem.product_name,
                    ShipmentItem.quality
                ).all()

                for item in query:
                    qty_delta = item.total_quantity * spec['multiplier']
                    db_item = db.query(CenterInventorySnapshotItemModel).filter(
                        and_(
                            CenterInventorySnapshotItemModel.center_inventory_snapshot_id == center_snapshot.id,
                            CenterInventorySnapshotItemModel.product_name == item.product_name,
                            CenterInventorySnapshotItemModel.quality == item.quality
                        )
                    ).first()
                    if db_item:
                        db_item.quantity += qty_delta
                        db_item.total_price = db_item.quantity * db_item.unit_price
                    else:
                        new_item = CenterInventorySnapshotItemModel(
                            id=uuid.uuid4(),
                            center_inventory_snapshot_id=center_snapshot.id,
                            product_name=item.product_name,
                            quantity=qty_delta,
                            quality=item.quality,
                            unit_price=item.avg_unit_price,
                            total_price=qty_delta * item.avg_unit_price,
                        )
                        db.add(new_item)

            # 총합 업데이트
            total_quantity = sum(item.quantity for item in center_snapshot.items)
            total_price = sum(item.total_price for item in center_snapshot.items)
            center_snapshot.total_quantity = total_quantity
            center_snapshot.total_price = total_price
        
        current_date += timedelta(days=1)
    
    db.commit()

def finalize_center_inventory_snapshot(
    db: Session,
    target_date: date,
    company_id: UUID,
    center_id: UUID
) -> CenterInventorySnapshot:
    """
    특정 날짜의 센터 인벤토리 스냅샷을 finalized 상태로 변경합니다.
    """
    # 해당 날짜의 스냅샷 조회
    snapshot = db.query(CenterInventorySnapshotModel).filter(
        and_(
            CenterInventorySnapshotModel.snapshot_date == target_date,
            CenterInventorySnapshotModel.center_id == center_id,
            CenterInventorySnapshotModel.company_id == company_id
        )
    ).first()
    
    if not snapshot:
        raise ValueError("해당 날짜의 스냅샷이 존재하지 않습니다.")
    
    # finalized 상태로 변경
    snapshot.finalized = True
    db.commit()
    
    # 아이템 변환
    items = db.query(CenterInventorySnapshotItemModel).filter(
        CenterInventorySnapshotItemModel.center_inventory_snapshot_id == snapshot.id
    ).all()
    snapshot_items = [
        InventorySnapshotItem(
            product_name=item.product_name,
            quality=item.quality,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.total_price
        ) for item in items
    ]
    
    return CenterInventorySnapshot(
        center_id=center_id,
        center_name=snapshot.center.name,
        total_quantity=snapshot.total_quantity,
        total_price=snapshot.total_price,
        items=snapshot_items
    )

def finalize_company_inventory_snapshot(
    db: Session,
    target_date: date,
    company_id: UUID
) -> DailyInventorySnapshot:
    """
    특정 날짜의 회사 전체 인벤토리 스냅샷을 finalized 상태로 변경합니다.
    """
    # 회사의 모든 센터 조회
    centers = db.query(Center).filter(Center.company_id == company_id).all()
    
    center_snapshots = []
    for center in centers:
        try:
            finalized_snapshot = finalize_center_inventory_snapshot(
                db, target_date, company_id, center.id
            )
            center_snapshots.append(finalized_snapshot)
        except ValueError:
            # 해당 센터의 스냅샷이 없는 경우 무시
            continue
    
    return DailyInventorySnapshot(
        snapshot_date=target_date,
        centers=center_snapshots
    )

def update_daily_inventory_snapshot(
    db: Session,
    update_request: UpdateDailyInventorySnapshotRequest,
    company_id: UUID,
    profile_id: UUID,
    contract_id: UUID = None
) -> Tuple[DailyInventorySnapshot, List[Shipment], List[Shipment]]:
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
            shipment = Shipment(
                title=f"인벤토리 조정 - {center_update.center_id}",
                creator_id=profile_id,
                supplier_company_id=company_id,
                departure_center_id=center_update.center_id,
                shipment_status="completed",
                shipment_datetime=update_request.snapshot_date,
                contract_id=contract_id
            )
            db.add(shipment)
            db.flush()
            for item in wholesale_items:
                shipment_item = ShipmentItem(
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
            shipment = Shipment(
                title=f"인벤토리 조정 - {center_update.center_id}",
                creator_id=profile_id,
                supplier_company_id=company_id,
                departure_center_id=center_update.center_id,
                shipment_status="completed",
                shipment_datetime=update_request.snapshot_date,
                contract_id=contract_id
            )
            db.add(shipment)
            db.flush()
            for item in retail_items:
                shipment_item = ShipmentItem(
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
    # 향후 30일까지만 업데이트하도록 제한
    max_future_days = 30
    next_date = update_request.snapshot_date + timedelta(days=1)
    days_processed = 0
    
    # 업데이트된 모든 센터 ID 수집
    updated_center_ids = [center_update.center_id for center_update in update_request.centers]
    
    while days_processed < max_future_days:
        # 모든 센터에 대해 다음 날짜의 스냅샷이 존재하는지 확인
        existing_snapshots = db.query(CenterInventorySnapshotModel).filter(
            and_(
                CenterInventorySnapshotModel.snapshot_date == next_date,
                CenterInventorySnapshotModel.company_id == company_id,
                CenterInventorySnapshotModel.center_id.in_(updated_center_ids)
            )
        ).all()
        
        if not existing_snapshots:
            # 더 이상 미래의 스냅샷이 없으면 종료
            break
            
        # 각 센터의 기존 스냅샷을 업데이트
        for center_id in updated_center_ids:
            create_daily_center_inventory_snapshot(db, next_date, company_id, center_id, profile_id, contract_id=contract_id)
        
        next_date = next_date + timedelta(days=1)
        days_processed += 1
    
    db.commit()
    
    # 업데이트된 스냅샷 반환
    updated_snapshot = get_daily_company_inventory_snapshot(db, update_request.snapshot_date, company_id)
    return updated_snapshot, created_shipments, created_shipments
