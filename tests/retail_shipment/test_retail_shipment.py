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
    # Override dependency to use test DB
    app.dependency_overrides[get_db] = lambda: db

    # Create base entities
    user = create_user(db)
    wholesaler = create_wholesaler(db, user=user)
    company = create_company(db, user_id=user.id)
    retailer = create_retailer(db, user_id=user.id)
    center = create_center(db, company_id=company.id)

    # Create a contract and an item for shipments
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

    # Authentication header
    access_token, _ = create_token_pair(user)
    headers = {"Authorization": f"Bearer {access_token}"}

    return {
        "company": company,
        "retailer": retailer,
        "center": center,
        "contract": contract,
        "headers": headers
    }


def test_get_shipments_empty(test_setup):
    # Should start with no shipments
    res = client.get("/retail-shipments/", headers=test_setup["headers"])
    assert res.status_code == 200
    assert res.json() == []


def test_create_shipment(test_setup):
    payload = {
        "retailer_id": str(test_setup["retailer"].id),
        "contract_id": str(test_setup["contract"].id),
        "center_id": str(test_setup["center"].id),
        "shipment_date": date.today().isoformat(),
        "shipment_name": "첫 출하",
        "items": [
            {
                "crop_name": "배",
                "quantity_kg": 5.0,
                "unit_price": 2000.0,
                "total_price": 10000.0,
                "quality_grade": "B"
            }
        ]
    }
    res = client.post("/retail-shipments/", json=payload, headers=test_setup["headers"])
    assert res.status_code == 200

    data = res.json()
    assert data["shipment_name"] == "첫 출하"
    assert len(data["items"]) == 1
    assert data["items"][0]["crop_name"] == "배"
    return data["id"]  # Return the ID for other tests


def test_get_shipment(test_setup):
    # Create a shipment first
    shipment_id = test_create_shipment(test_setup)
    
    # Get the shipment
    res = client.get(f"/retail-shipments/{shipment_id}", headers=test_setup["headers"])
    assert res.status_code == 200
    assert res.json()["id"] == shipment_id


def test_finalize_and_delete_shipment(test_setup):
    # Create a shipment first
    shipment_id = test_create_shipment(test_setup)
    
    # Finalize
    res = client.post(f"/retail-shipments/{shipment_id}/finalize", headers=test_setup["headers"])
    assert res.status_code == 200
    assert res.json()["is_finalized"] is True

    # Delete
    res2 = client.delete(f"/retail-shipments/{shipment_id}", headers=test_setup["headers"])
    assert res2.status_code == 200

    # After delete, getting it should 404
    res3 = client.get(f"/retail-shipments/{shipment_id}", headers=test_setup["headers"])
    assert res3.status_code == 404


def test_shipment_items_and_progress(test_setup):
    # Create a shipment
    payload = {
        "retailer_id": str(test_setup["retailer"].id),
        "contract_id": str(test_setup["contract"].id),
        "center_id": str(test_setup["center"].id),
        "shipment_date": date.today().isoformat(),
        "shipment_name": "두번째 출하",
        "items": [
            {
                "crop_name": "사과",
                "quantity_kg": 3.0,
                "unit_price": 1000.0,
                "total_price": 3000.0
            }
        ]
    }
    res = client.post("/retail-shipments/", json=payload, headers=test_setup["headers"])
    assert res.status_code == 200
    shipment_id = res.json()["id"]

    # Get items
    res_items = client.get(f"/retail-shipments/{shipment_id}/items", headers=test_setup["headers"])
    assert res_items.status_code == 200
    items = res_items.json()
    assert len(items) == 1
    assert items[0]["crop_name"] == "사과"

    # Get contract shipments
    contract_id = test_setup["contract"].id
    res_contract = client.get(f"/retail-shipments/contracts/{contract_id}/shipments", headers=test_setup["headers"])
    assert res_contract.status_code == 200
    assert any(s["id"] == shipment_id for s in res_contract.json())

    # Get shipment progress
    res_progress = client.get(f"/retail-shipments/contracts/{contract_id}/shipment-progress", headers=test_setup["headers"])
    assert res_progress.status_code == 200
    progress = res_progress.json()
    assert isinstance(progress, list)


def test_retailer_and_company_shipments(test_setup):
    # Create a shipment first
    shipment_id = test_create_shipment(test_setup)
    
    # Retailer shipments
    retailer_id = test_setup["retailer"].id
    res_r = client.get(f"/retail-shipments/retailers/{retailer_id}/shipments", headers=test_setup["headers"])
    assert res_r.status_code == 200
    assert any(s["id"] == shipment_id for s in res_r.json())

    # My company shipments
    res_c = client.get("/retail-shipments/my-company/shipments", headers=test_setup["headers"])
    assert res_c.status_code == 200
    assert any(s["id"] == shipment_id for s in res_c.json())