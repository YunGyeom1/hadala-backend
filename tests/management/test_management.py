import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta
from uuid import UUID

from tests.factories import (
    create_user,
    create_company,
    create_wholesaler,
    create_center,
    create_inventory,
    create_inventory_item,
    create_token_pair
)

@pytest.fixture
def test_setup(db: Session, client: TestClient):
    user = create_user(db)
    wholesaler = create_wholesaler(db, user)
    company = create_company(db, user.id)
    center = create_center(db, company.id)
    access_token, _ = create_token_pair(user)
    headers = {"Authorization": f"Bearer {access_token}"}
    
    return {
        "user": user,
        "company": company,
        "wholesaler": wholesaler,
        "center": center,
        "headers": headers,
        "db": db,
        "client": client,
    }

def test_calculate_settlement(test_setup):
    client = test_setup["client"]
    center = test_setup["center"]
    headers = test_setup["headers"]
    today = date.today()

    # 인벤토리 데이터 생성
    inventory = create_inventory(test_setup["db"], test_setup["company"].id, center.id, today)
    create_inventory_item(test_setup["db"], inventory.id, "상추", "A", 100.0)
    create_inventory_item(test_setup["db"], inventory.id, "배추", "B", 80.0)

    # 정산 계산
    response = client.post(
        f"/management/settlements/calculate?center_id={center.id}&target_date={today}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["date"] == str(today)
    assert data["center_id"] == str(center.id)
    assert "total_wholesale_in_kg" in data
    assert "total_retail_out_kg" in data

def test_get_settlements(test_setup):
    client = test_setup["client"]
    center = test_setup["center"]
    headers = test_setup["headers"]
    today = date.today()

    # 여러 날짜의 정산 데이터 생성
    for i in range(3):
        target_date = today - timedelta(days=i)
        inventory = create_inventory(test_setup["db"], test_setup["company"].id, center.id, target_date)
        create_inventory_item(test_setup["db"], inventory.id, f"채소{i}", "A", 10.0)
        
        client.post(
            f"/management/settlements/calculate?center_id={center.id}&target_date={target_date}",
            headers=headers
        )

    # 정산 목록 조회
    response = client.get(
        f"/management/settlements?start_date={today - timedelta(days=2)}&end_date={today}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3

def test_get_settlement(test_setup):
    client = test_setup["client"]
    center = test_setup["center"]
    headers = test_setup["headers"]
    today = date.today()

    # 정산 데이터 생성
    inventory = create_inventory(test_setup["db"], test_setup["company"].id, center.id, today)
    create_inventory_item(test_setup["db"], inventory.id, "상추", "A", 100.0)
    
    settlement = client.post(
        f"/management/settlements/calculate?center_id={center.id}&target_date={today}",
        headers=headers
    ).json()

    # 특정 정산 조회
    response = client.get(f"/management/settlements/{settlement['id']}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == settlement["id"]
    assert data["date"] == str(today)

def test_update_settlement(test_setup):
    client = test_setup["client"]
    center = test_setup["center"]
    headers = test_setup["headers"]
    today = date.today()

    # 정산 데이터 생성
    inventory = create_inventory(test_setup["db"], test_setup["company"].id, center.id, today)
    create_inventory_item(test_setup["db"], inventory.id, "상추", "A", 100.0)
    
    settlement = client.post(
        f"/management/settlements/calculate?center_id={center.id}&target_date={today}",
        headers=headers
    ).json()

    # 정산 업데이트
    update_data = {
        "total_wholesale_in_kg": 150.0,
        "total_retail_out_kg": 120.0,
        "discrepancy_in_kg": 30.0
    }
    response = client.put(
        f"/management/settlements/{settlement['id']}",
        json=update_data,
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_wholesale_in_kg"] == 150.0
    assert data["total_retail_out_kg"] == 120.0
    assert data["discrepancy_in_kg"] == 30.0

def test_calculate_accounting(test_setup):
    client = test_setup["client"]
    headers = test_setup["headers"]
    today = date.today()

    # 회계 계산
    response = client.post(
        f"/management/accounting/calculate?target_date={today}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["date"] == str(today)
    assert "total_prepaid" in data
    assert "total_pre_received" in data
    assert "total_paid" in data
    assert "total_received" in data

def test_get_accountings(test_setup):
    client = test_setup["client"]
    headers = test_setup["headers"]
    today = date.today()

    # 여러 날짜의 회계 데이터 생성
    for i in range(3):
        target_date = today - timedelta(days=i)
        client.post(
            f"/management/accounting/calculate?target_date={target_date}",
            headers=headers
        )

    # 회계 목록 조회
    response = client.get(
        f"/management/accounting?start_date={today - timedelta(days=2)}&end_date={today}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3

def test_get_accounting(test_setup):
    client = test_setup["client"]
    headers = test_setup["headers"]
    today = date.today()

    # 회계 데이터 생성
    accounting = client.post(
        f"/management/accounting/calculate?target_date={today}",
        headers=headers
    ).json()

    # 특정 회계 조회
    response = client.get(f"/management/accounting/{accounting['id']}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == accounting["id"]
    assert data["date"] == str(today)

def test_update_accounting(test_setup):
    client = test_setup["client"]
    headers = test_setup["headers"]
    today = date.today()

    # 회계 데이터 생성
    accounting = client.post(
        f"/management/accounting/calculate?target_date={today}",
        headers=headers
    ).json()

    # 회계 업데이트
    update_data = {
        "total_prepaid": 1000000.0,
        "total_pre_received": 800000.0,
        "total_paid": 500000.0,
        "total_received": 400000.0
    }
    response = client.put(
        f"/management/accounting/{accounting['id']}",
        json=update_data,
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_prepaid"] == 1000000.0
    assert data["total_pre_received"] == 800000.0
    assert data["total_paid"] == 500000.0
    assert data["total_received"] == 400000.0

def test_create_today_settlement(test_setup):
    client = test_setup["client"]
    center = test_setup["center"]
    headers = test_setup["headers"]
    today = date.today()

    # 오늘 날짜의 인벤토리 생성
    inventory = create_inventory(test_setup["db"], test_setup["company"].id, center.id, today)
    create_inventory_item(test_setup["db"], inventory.id, "상추", "A", 100.0)
    create_inventory_item(test_setup["db"], inventory.id, "배추", "B", 80.0)

    # 오늘자 결산 생성
    response = client.post("/management/settlements/today", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["date"] == str(today)
    assert "total_wholesale_in_kg" in data
    assert "total_retail_out_kg" in data

def test_create_today_settlement_for_center(test_setup):
    client = test_setup["client"]
    center = test_setup["center"]
    headers = test_setup["headers"]
    today = date.today()

    # 특정 센터의 오늘 날짜 인벤토리 생성
    inventory = create_inventory(test_setup["db"], test_setup["company"].id, center.id, today)
    create_inventory_item(test_setup["db"], inventory.id, "상추", "A", 100.0)
    create_inventory_item(test_setup["db"], inventory.id, "배추", "B", 80.0)

    # 특정 센터의 오늘자 결산 생성
    response = client.post(f"/management/settlements/today/center/{center.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["date"] == str(today)
    assert data["center_id"] == str(center.id)
    assert "total_wholesale_in_kg" in data
    assert "total_retail_out_kg" in data 