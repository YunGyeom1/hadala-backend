import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta
from uuid import UUID

from app.main import app
from app.database.session import get_db
from tests.factories import (
    create_user, create_wholesaler, create_company, create_retailer,
    create_center, create_retail_contract, create_retail_contract_item,
    create_token_pair
)

client = TestClient(app)

@pytest.fixture
def test_setup(db: Session, client: TestClient):
    # DB 의존성 오버라이드
    app.dependency_overrides[get_db] = lambda: db

    # 기본 엔터티 생성
    user = create_user(db)
    wholesaler = create_wholesaler(db, user=user)
    company = create_company(db, user_id=user.id)
    retailer = create_retailer(db, user_id=user.id)
    center = create_center(db, company_id=company.id)

    # 계약 및 아이템 생성
    contract = create_retail_contract(
        db,
        company_id=company.id,
        wholesaler_id=wholesaler.id,
        retailer_id=retailer.id,
        center_id=center.id,
        contract_date=date.today(),
        shipment_date=date.today() + timedelta(days=1),
        note="테스트 계약"
    )
    item = create_retail_contract_item(
        db,
        contract_id=contract.id,
        crop_name="사과",
        quantity_kg=10.0,
        unit_price=1000.0,
        quality_required="A"
    )

    # 인증 헤더
    access_token, _ = create_token_pair(user)
    headers = {"Authorization": f"Bearer {access_token}"}

    return {
        "db": db,
        "user": user,
        "wholesaler": wholesaler,
        "company": company,
        "retailer": retailer,
        "center": center,
        "contract": contract,
        "item": item,
        "headers": headers
    }

def test_create_contract(test_setup):
    payload = {
        "company_id": str(test_setup["company"].id),
        "wholesaler_id": str(test_setup["wholesaler"].id),
        "retailer_id": str(test_setup["retailer"].id),
        "center_id": str(test_setup["center"].id),
        "contract_date": date.today().isoformat(),
        "shipment_date": (date.today() + timedelta(days=1)).isoformat(),
        "note": "신규 계약",
        "items": [
            {
                "crop_name": "배",
                "quantity_kg": 5.0,
                "unit_price": 2000.0,
                "quality_required": "B"
            }
        ]
    }
    res = client.post("/retail-contracts/", json=payload, headers=test_setup["headers"])
    assert res.status_code == 200
    data = res.json()
    assert data["company_id"] == str(test_setup["company"].id)
    assert data["items"][0]["crop_name"] == "배"

def test_get_contract(test_setup):
    cid = test_setup["contract"].id
    res = client.get(f"/retail-contracts/{cid}", headers=test_setup["headers"])
    assert res.status_code == 200
    assert res.json()["id"] == str(cid)

def test_update_contract(test_setup):
    cid = test_setup["contract"].id
    res = client.put(
        f"/retail-contracts/{cid}",
        json={"note": "수정된 계약"},
        headers=test_setup["headers"]
    )
    assert res.status_code == 200
    assert res.json()["note"] == "수정된 계약"

def test_delete_contract(test_setup):
    cid = test_setup["contract"].id
    res = client.delete(f"/retail-contracts/{cid}", headers=test_setup["headers"])
    assert res.status_code == 200
    # 삭제 후 조회 시 404
    res2 = client.get(f"/retail-contracts/{cid}", headers=test_setup["headers"])
    assert res2.status_code == 404

def test_create_and_get_item(test_setup):
    cid = test_setup["contract"].id
    payload = {
        "crop_name": "귤",
        "quantity_kg": 3.0,
        "unit_price": 500.0,
        "quality_required": "C"
    }
    res = client.post(f"/retail-contracts/{cid}/items", json=payload, headers=test_setup["headers"])
    assert res.status_code == 200
    iid = res.json()["id"]

    res2 = client.get(f"/retail-contracts/items/{iid}", headers=test_setup["headers"])
    assert res2.status_code == 200
    assert res2.json()["crop_name"] == "귤"

def test_update_and_delete_item(test_setup):
    iid = test_setup["item"].id
    res = client.put(
        f"/retail-contracts/items/{iid}",
        json={"quantity_kg": 20.0},
        headers=test_setup["headers"]
    )
    assert res.status_code == 200
    assert res.json()["quantity_kg"] == 20.0

    res2 = client.delete(f"/retail-contracts/items/{iid}", headers=test_setup["headers"])
    assert res2.status_code == 200
    # 삭제 후 조회 시 404
    res3 = client.get(f"/retail-contracts/items/{iid}", headers=test_setup["headers"])
    assert res3.status_code == 404

def test_list_payment_logs_empty(test_setup):
    cid = test_setup["contract"].id
    res = client.get(f"/retail-contracts/{cid}/payment-logs", headers=test_setup["headers"])
    assert res.status_code == 200
    assert res.json() == []

def test_get_nonexistent_payment_log(test_setup):
    fake_id = UUID("00000000-0000-0000-0000-000000000000")
    res = client.get(f"/retail-contracts/payment-logs/{fake_id}", headers=test_setup["headers"])
    assert res.status_code == 404