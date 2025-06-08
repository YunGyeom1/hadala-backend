import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta

from tests.factories import (
    create_user,
    create_company,
    create_wholesaler,
    create_center,
    create_inventory,
    create_inventory_item,
    create_token_pair,
    add_company_wholesaler
)

@pytest.fixture
def test_setup(db: Session, client: TestClient):
    user = create_user(db)
    wholesaler = create_wholesaler(db, user)
    company = create_company(db, user.id)
    wholesaler.company_id = company.id
    db.commit()
    db.refresh(wholesaler)

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


def test_create_inventory_snapshot(test_setup):
    client = test_setup["client"]
    center = test_setup["center"]
    headers = test_setup["headers"]

    payload = {
        "date": str(date.today()),
        "center_id": str(center.id),
        "items": [
            {"crop_name": "상추", "quality_grade": "A", "quantity": 100.0},
            {"crop_name": "배추", "quality_grade": "B", "quantity": 80.5}
        ]
    }
    response = client.post("/inventories/snapshots", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["center_id"] == str(center.id)
    assert len(data["items"]) == 2


def test_get_inventory_snapshot(test_setup):
    client = test_setup["client"]
    center = test_setup["center"]
    headers = test_setup["headers"]

    snapshot = client.post("/inventories/snapshots", json={
        "date": str(date.today()),
        "center_id": str(center.id),
        "items": [{"crop_name": "무", "quality_grade": "A", "quantity": 30.0}]
    }, headers=headers).json()

    response = client.get(f"/inventories/snapshots/{snapshot['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == snapshot["id"]


def test_add_inventory_item(test_setup):
    client = test_setup["client"]
    center = test_setup["center"]
    headers = test_setup["headers"]

    snapshot_id = client.post("/inventories/snapshots", json={
        "date": str(date.today()),
        "center_id": str(center.id),
        "items": []
    }, headers=headers).json()["id"]

    item_payload = {"crop_name": "토마토", "quality_grade": "C", "quantity": 44.4}
    response = client.post(f"/inventories/snapshots/{snapshot_id}/items", json=item_payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["crop_name"] == "토마토"


def test_get_inventory_items(test_setup):
    client = test_setup["client"]
    center = test_setup["center"]
    headers = test_setup["headers"]

    snapshot_id = client.post("/inventories/snapshots", json={
        "date": str(date.today()),
        "center_id": str(center.id),
        "items": [{"crop_name": "감자", "quality_grade": "A", "quantity": 20.0}]
    }, headers=headers).json()["id"]

    response = client.get(f"/inventories/snapshots/{snapshot_id}/items", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_inventory_filtering(test_setup):
    db = test_setup["db"]
    client = test_setup["client"]
    company = test_setup["company"]
    center = test_setup["center"]
    headers = test_setup["headers"]

    inventory = create_inventory(db, company.id, center.id)
    create_inventory_item(db, inventory.id, crop_name="상추", quality_grade="B")

    response = client.get("/inventories/snapshots?crop_name=상추&quality_grade=B", headers=headers)
    assert response.status_code == 200
    assert any(i["id"] == str(inventory.id) for i in response.json())


def test_delete_inventory_item(test_setup):
    db = test_setup["db"]
    client = test_setup["client"]
    company = test_setup["company"]
    center = test_setup["center"]
    headers = test_setup["headers"]

    inventory = create_inventory(db, company.id, center.id)
    item = create_inventory_item(db, inventory.id, crop_name="무", quality_grade="A")

    response = client.delete(f"/inventories/items/{item.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Inventory item deleted successfully"


def test_update_inventory_item(test_setup):
    client = test_setup["client"]
    center = test_setup["center"]
    headers = test_setup["headers"]

    # 인벤토리 스냅샷 생성
    snapshot = client.post("/inventories/snapshots", json={
        "date": str(date.today()),
        "center_id": str(center.id),
        "items": [{"crop_name": "당근", "quality_grade": "B", "quantity": 50.0}]
    }, headers=headers).json()

    # 아이템 업데이트
    item_id = snapshot["items"][0]["id"]
    update_payload = {
        "crop_name": "당근",
        "quality_grade": "A",
        "quantity": 45.0
    }
    response = client.put(f"/inventories/items/{item_id}", json=update_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["quality_grade"] == "A"
    assert data["quantity"] == 45.0


def test_get_company_inventories(test_setup):
    client = test_setup["client"]
    center = test_setup["center"]
    headers = test_setup["headers"]

    # 여러 인벤토리 스냅샷 생성
    for i in range(3):
        client.post("/inventories/snapshots", json={
            "date": str(date.today()),
            "center_id": str(center.id),
            "items": [{"crop_name": f"채소{i}", "quality_grade": "A", "quantity": 10.0}]
        }, headers=headers)

    response = client.get("/inventories/my-company/inventories", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


def test_get_company_inventories_by_date(test_setup):
    client = test_setup["client"]
    center = test_setup["center"]
    headers = test_setup["headers"]
    today = date.today()

    # 오늘 날짜의 인벤토리 생성
    client.post("/inventories/snapshots", json={
        "date": str(today),
        "center_id": str(center.id),
        "items": [{"crop_name": "오늘채소", "quality_grade": "A", "quantity": 10.0}]
    }, headers=headers)

    # 어제 날짜의 인벤토리 생성
    yesterday = today - timedelta(days=1)
    client.post("/inventories/snapshots", json={
        "date": str(yesterday),
        "center_id": str(center.id),
        "items": [{"crop_name": "어제채소", "quality_grade": "A", "quantity": 10.0}]
    }, headers=headers)

    # 오늘 날짜의 인벤토리 조회
    response = client.get(f"/inventories/my-company/inventories/{today}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(item["date"] == str(today) for item in data)


def test_create_today_settlement(test_setup):
    client = test_setup["client"]
    center = test_setup["center"]
    headers = test_setup["headers"]

    client.post("/inventories/snapshots", json={
        "date": str(date.today()),
        "center_id": str(center.id),
        "items": [
            {"crop_name": "상추", "quality_grade": "A", "quantity": 100.0},
            {"crop_name": "배추", "quality_grade": "B", "quantity": 80.0}
        ]
    }, headers=headers)

    response = client.post("/inventories/settlements/today/center/" + str(center.id), headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert "date" in data
    assert "total_wholesale_in_kg" in data
    assert "total_retail_out_kg" in data
    assert "discrepancy_in_kg" in data

def test_create_today_settlement_for_center(test_setup):
    client = test_setup["client"]
    center = test_setup["center"]
    headers = test_setup["headers"]

    # 특정 센터의 오늘 날짜 인벤토리 생성
    client.post("/inventories/snapshots", json={
        "date": str(date.today()),
        "center_id": str(center.id),
        "items": [
            {"crop_name": "상추", "quality_grade": "A", "quantity": 100.0},
            {"crop_name": "배추", "quality_grade": "B", "quantity": 80.0}
        ]
    }, headers=headers)

    # 특정 센터의 오늘자 결산 생성
    response = client.post(f"/inventories/settlements/today/center/{center.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()

    # 필드 검증 (스키마 기반으로)
    assert "date" in data
    assert "center_id" in data
    assert data["center_id"] == str(center.id)
    assert "total_wholesale_in_kg" in data
    assert "total_retail_out_kg" in data
    assert "discrepancy_in_kg" in data or "discrepancy_out_kg" in data