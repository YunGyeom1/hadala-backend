import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta
from uuid import UUID

from app.main import app
from app.database.session import get_db
from tests.factories import (
    create_user, create_wholesaler, create_company, create_farmer,
    create_center, create_wholesale_contract, create_wholesale_contract_item,
    create_token_pair
)

client = TestClient(app)

@pytest.fixture
def test_setup(db: Session):
    """테스트용 기본 데이터 생성, DB 의존성 오버라이드 및 인증 헤더 반환"""
    # DB 의존성 오버라이드
    app.dependency_overrides[get_db] = lambda: db

    # 유저 및 도매상, 회사, 농부, 센터, 계약, 품목 생성
    user = create_user(db)
    wholesaler = create_wholesaler(db, user=user)
    company = create_company(db, user_id=user.id)
    farmer = create_farmer(db)
    center = create_center(db, company_id=company.id)
    contract = create_wholesale_contract(
        db,
        center_id=center.id,
        wholesaler_id=wholesaler.id,
        farmer_id=farmer.id,
        company_id=company.id
    )
    item = create_wholesale_contract_item(db, contract_id=contract.id)
    
    # 인증 토큰 생성
    access_token, _ = create_token_pair(user)
    headers = {"Authorization": f"Bearer {access_token}"}

    return {
        "db": db,
        "user": user,
        "wholesaler": wholesaler,
        "company": company,
        "farmer": farmer,
        "center": center,
        "contract": contract,
        "item": item,
        "headers": headers,
    }


def test_create_and_get_shipment_from_contract(test_setup):
    contract = test_setup["contract"]
    item = test_setup["item"]
    payload = {
        "contract_id": str(contract.id),
        "farmer_id": str(test_setup["farmer"].id),
        "center_id": str(test_setup["center"].id),
        "wholesaler_id": str(test_setup["wholesaler"].id),
        "shipment_date": date.today().isoformat(),
        "items": [
            {
                "crop_name": item.crop_name,
                "quantity": item.quantity_kg,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "quality_grade": item.quality_required,
            }
        ],
    }
    res = client.post(
        f"/wholesale-shipments/from-contract/{contract.id}",
        json=payload,
        headers=test_setup["headers"],
    )
    assert res.status_code == 200
    data = res.json()
    shipment_id = data["id"]
    assert data["contract_id"] == str(contract.id)
    assert data["is_finalized"] is False

    # 생성된 출고 단건 조회
    get_res = client.get(
        f"/wholesale-shipments/{shipment_id}",
        headers=test_setup["headers"],
    )
    assert get_res.status_code == 200
    got = get_res.json()
    assert got["id"] == shipment_id
    assert got["items"][0]["crop_name"] == item.crop_name


def test_list_and_contract_shipments(test_setup):
    # 출고 하나 삽입
    from app.wholesale_shipment.crud import create_shipment_from_contract
    from app.wholesale_shipment.schemas import WholesaleShipmentCreate, WholesaleShipmentItemCreate

    item = test_setup["item"]
    contract = test_setup["contract"]
    shipment_data = WholesaleShipmentCreate(
        contract_id=contract.id,
        farmer_id=test_setup["farmer"].id,
        center_id=test_setup["center"].id,
        wholesaler_id=test_setup["wholesaler"].id,
        shipment_date=date.today(),
        total_price=item.total_price,
        items=[
            WholesaleShipmentItemCreate(
                crop_name=item.crop_name,
                quantity=item.quantity_kg,
                unit_price=item.unit_price,
                total_price=item.total_price,
                quality_grade=item.quality_required
            )
        ]
    )
    create_shipment_from_contract(
        db=test_setup["db"],
        contract_id=contract.id,
        shipment=shipment_data,
        company_id=test_setup["company"].id
    )

    # 전체 출고 리스트 조회
    res = client.get(
        "/wholesale-shipments/",
        headers=test_setup["headers"],
    )
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # 특정 계약 출고 목록 조회
    contract_id = test_setup["contract"].id
    res2 = client.get(
        f"/wholesale-shipments/contracts/{contract_id}/shipments",
        headers=test_setup["headers"],
    )
    assert res2.status_code == 200
    assert isinstance(res2.json(), list)


def test_shipment_progress(test_setup):
    # 계약별 출고 진행 통계 조회
    contract_id = test_setup["contract"].id
    today = date.today()
    params = {
        "start_date": (today - timedelta(days=1)).isoformat(),
        "end_date": today.isoformat()
    }
    res = client.get(
        f"/wholesale-shipments/contracts/{contract_id}/shipment-progress",
        params=params,
        headers=test_setup["headers"],
    )
    assert res.status_code == 200
    prog = res.json()
    assert prog["contract_id"] == str(contract_id)
    assert "total_shipped_amount" in prog


def test_finalize_and_delete_shipment(test_setup):
    # 출고 생성
    payload = {
        "contract_id": str(test_setup["contract"].id),
        "farmer_id": str(test_setup["farmer"].id),
        "center_id": str(test_setup["center"].id),
        "wholesaler_id": str(test_setup["wholesaler"].id),
        "shipment_date": date.today().isoformat(),
        "items": [
            {
                "crop_name": test_setup["item"].crop_name,
                "quantity": test_setup["item"].quantity_kg,
                "unit_price": test_setup["item"].unit_price,
                "total_price": test_setup["item"].total_price,
                "quality_grade": test_setup["item"].quality_required,
            }
        ],
    }
    create_res = client.post(
        "/wholesale-shipments/",
        json=payload,
        headers=test_setup["headers"],
    )
    assert create_res.status_code == 200
    sid = create_res.json()["id"]

    # 출고 완료 처리
    fin_res = client.post(
        f"/wholesale-shipments/{sid}/finalize",
        headers=test_setup["headers"],
    )
    assert fin_res.status_code == 200
    assert fin_res.json()["is_finalized"] is True

    # 이미 완료된 출고 재완료 시 404 예상
    fin2 = client.post(
        f"/wholesale-shipments/{sid}/finalize",
        headers=test_setup["headers"],
    )
    assert fin2.status_code == 404

    # 출고 삭제 (완료된 출고는 삭제 불가, 404 기대)
    del_res = client.delete(
        f"/wholesale-shipments/{sid}",
        headers=test_setup["headers"],
    )
    assert del_res.status_code == 404