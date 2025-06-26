from app.database.session import SessionLocal
from app.company.inventory_snapshot.crud import get_daily_company_inventory_snapshot
from datetime import date
from sqlalchemy import func, cast, Date
from app.transactions.shipment.models import Shipment, ShipmentItem
from app.company.center.models import Center

def test_inventory_snapshot():
    db = SessionLocal()
    target_date = date(2025, 6, 26)
    company_id = 'e6b75a92-ae7f-4aaf-a772-6348f1da1805'
    
    print('=== 재고 스냅샷 조회 ===')
    print(f'날짜: {target_date}')
    print(f'회사 ID: {company_id}')
    
    try:
        snapshot = get_daily_company_inventory_snapshot(db, target_date, company_id)
        print(f'스냅샷: {snapshot}')
        
        if snapshot:
            print(f'센터 개수: {len(snapshot.centers)}')
            for center in snapshot.centers:
                print(f'센터: {center.center_name}, 총 수량: {center.total_quantity}, 총 가격: {center.total_price}')
                print(f'  아이템 개수: {len(center.items)}')
                for item in center.items:
                    print(f'    - {item.product_name} ({item.quality}): {item.quantity}개, {item.unit_price}원')
        else:
            print('스냅샷이 None입니다.')
            
    except Exception as e:
        print(f'에러 발생: {e}')
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def test_manual_inventory_calc():
    db = SessionLocal()
    company_id = 'e6b75a92-ae7f-4aaf-a772-6348f1da1805'
    target_date = date(2025, 6, 26)
    print('\n=== shipment 데이터로 직접 재고 계산 ===')
    centers = db.query(Center).filter(Center.company_id == company_id).all()
    for center in centers:
        print(f'\n센터: {center.name}')
        # 품목별 재고 dict
        inventory = {}
        # 출하(−)
        departure_items = db.query(ShipmentItem.product_name, ShipmentItem.quality, func.sum(ShipmentItem.quantity).label('total_quantity'), func.avg(ShipmentItem.unit_price).label('avg_unit_price')).join(Shipment, ShipmentItem.shipment_id == Shipment.id).filter(
            Shipment.supplier_company_id == company_id,
            Shipment.departure_center_id == center.id,
            cast(Shipment.shipment_datetime, Date) <= target_date
        ).group_by(ShipmentItem.product_name, ShipmentItem.quality).all()
        for item in departure_items:
            key = (item.product_name, item.quality)
            inventory.setdefault(key, {'quantity': 0, 'unit_price': item.avg_unit_price})
            inventory[key]['quantity'] -= item.total_quantity
        # 입하(+)
        arrival_items = db.query(ShipmentItem.product_name, ShipmentItem.quality, func.sum(ShipmentItem.quantity).label('total_quantity'), func.avg(ShipmentItem.unit_price).label('avg_unit_price')).join(Shipment, ShipmentItem.shipment_id == Shipment.id).filter(
            Shipment.supplier_company_id == company_id,
            Shipment.arrival_center_id == center.id,
            cast(Shipment.shipment_datetime, Date) <= target_date
        ).group_by(ShipmentItem.product_name, ShipmentItem.quality).all()
        for item in arrival_items:
            key = (item.product_name, item.quality)
            inventory.setdefault(key, {'quantity': 0, 'unit_price': item.avg_unit_price})
            inventory[key]['quantity'] += item.total_quantity
        # 결과 출력
        total_quantity = 0
        total_price = 0
        for (product_name, quality), v in inventory.items():
            print(f'  - {product_name}({quality}): {v["quantity"]}개, 단가 {v["unit_price"]}원, 금액 {v["quantity"]*v["unit_price"]}원')
            total_quantity += v['quantity']
            total_price += v['quantity'] * v['unit_price']
        print(f'  ▶︎ 총 수량: {total_quantity}, 총 금액: {total_price}')
    db.close()

def print_all_shipments():
    db = SessionLocal()
    print('\n=== 전체 shipment 및 아이템 출력 ===')
    shipments = db.query(Shipment).all()
    print(f'총 shipment 개수: {len(shipments)}')
    for shipment in shipments:
        print(f'\nShipment ID: {shipment.id}')
        print(f'  제목: {shipment.title}')
        print(f'  출발 센터: {shipment.departure_center_id}')
        print(f'  도착 센터: {shipment.arrival_center_id}')
        print(f'  공급사: {shipment.supplier_company_id}')
        print(f'  날짜: {shipment.shipment_datetime}')
        print(f'  상태: {shipment.shipment_status}')
        items = db.query(ShipmentItem).filter(ShipmentItem.shipment_id == shipment.id).all()
        print(f'  아이템 개수: {len(items)}')
        for item in items:
            print(f'    - {item.product_name} ({item.quality}): {item.quantity}개, {item.unit_price}원')
    db.close()

def test_correct_company_inventory():
    db = SessionLocal()
    target_date = date(2025, 6, 26)
    # shipment 데이터의 실제 supplier_company_id 사용
    correct_company_id = '626e8505-3d13-4bd1-a4e9-dff66f5c0902'
    
    print('\n=== 올바른 회사 ID로 재고 스냅샷 조회 ===')
    print(f'날짜: {target_date}')
    print(f'회사 ID: {correct_company_id}')
    
    try:
        snapshot = get_daily_company_inventory_snapshot(db, target_date, correct_company_id)
        print(f'스냅샷: {snapshot}')
        
        if snapshot:
            print(f'센터 개수: {len(snapshot.centers)}')
            for center in snapshot.centers:
                print(f'센터: {center.center_name}, 총 수량: {center.total_quantity}, 총 가격: {center.total_price}')
                print(f'  아이템 개수: {len(center.items)}')
                for item in center.items:
                    print(f'    - {item.product_name} ({item.quality}): {item.quantity}개, {item.unit_price}원')
        else:
            print('스냅샷이 None입니다.')
            
    except Exception as e:
        print(f'에러 발생: {e}')
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def check_shipment_details():
    db = SessionLocal()
    print('\n=== 현재 Shipment 데이터 상세 ===')
    shipments = db.query(Shipment).all()
    for shipment in shipments:
        print(f'ID: {shipment.id}, 제목: {shipment.title}')
        print(f'  공급자: {shipment.supplier_person_id}')
        print(f'  수신자: {shipment.receiver_person_id}')
        print(f'  공급회사: {shipment.supplier_company_id}')
        print(f'  수신회사: {shipment.receiver_company_id}')
        print(f'  출발센터: {shipment.departure_center_id}')
        print(f'  도착센터: {shipment.arrival_center_id}')
        print()
    db.close()

def test_multiple_dates():
    db = SessionLocal()
    company_id = 'e6b75a92-ae7f-4aaf-a772-6348f1da1805'
    
    print('\n=== 여러 날짜 재고 스냅샷 확인 ===')
    for test_date in [date(2025, 6, 24), date(2025, 6, 25), date(2025, 6, 26)]:
        print(f'\n--- {test_date} ---')
        try:
            snapshot = get_daily_company_inventory_snapshot(db, test_date, company_id)
            if snapshot:
                print(f'센터 개수: {len(snapshot.centers)}')
                for center in snapshot.centers:
                    print(f'센터: {center.center_name}, 총 수량: {center.total_quantity}, 총 가격: {center.total_price}')
                    print(f'  아이템 개수: {len(center.items)}')
                    for item in center.items:
                        print(f'    - {item.product_name} ({item.quality}): {item.quantity}개, {item.unit_price}원')
            else:
                print('스냅샷이 None입니다.')
        except Exception as e:
            print(f'에러: {e}')
    
    db.close()

if __name__ == "__main__":
    test_inventory_snapshot()
    test_manual_inventory_calc()
    print_all_shipments()
    test_correct_company_inventory()
    check_shipment_details()
    test_multiple_dates() 