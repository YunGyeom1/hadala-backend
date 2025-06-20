import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi import status
from sqlalchemy.orm import Session

from tests.factories import (
    ProfileFactory, CompanyFactory, CenterFactory, 
    ContractFactory, ShipmentFactory, TestDataFactory
)
from app.profile.models import ProfileRole
from app.transactions.common.models import ShipmentStatus, ProductQuality


class TestShipmentAPI:
    """Shipment API 테스트 클래스"""

    def test_create_shipment_success(self, client, db: Session):
        """출하 생성 성공 테스트"""
        # 테스트 데이터 준비
        setup = TestDataFactory.create_complete_user_setup(db, username="creator")
        creator = setup["profile"]
        user = setup["user"]
        supplier_company = setup["company"]
        
        buyer_company = CompanyFactory.create_company(db, name="구매 회사")
        
        # 계약 생성
        from app.core.auth.dependencies import get_current_user
        client.app.dependency_overrides[get_current_user] = lambda: user
        contract_data = ContractFactory.create_complete_contract(
            db, supplier_company.id, buyer_company.id, creator.id
        )
        contract = contract_data["contract"]
        
        # 출하 생성 요청 데이터
        shipment_data = {
            "title": "테스트 출하",
            "contract_id": str(contract.id),
            "supplier_company_id": str(supplier_company.id),
            "receiver_company_id": str(buyer_company.id),
            "shipment_datetime": datetime.now().isoformat(),
            "shipment_status": "pending",
            "items": [
                {
                    "shipment_id": str(uuid4()),  # 임시 ID, 실제로는 무시됨
                    "product_name": "쌀",
                    "quality": "A",
                    "quantity": 50,
                    "unit_price": 10000.0,
                    "total_price": 500000.0
                }
            ]
        }
        
        # API 호출
        response = client.post(
            "/shipments/",
            json=shipment_data,
            headers={"X-Profile-ID": str(creator.id)}
        )
        
        # 검증
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "테스트 출하"
        assert data["contract_id"] == str(contract.id)
        assert len(data["items"]) == 1
        assert data["items"][0]["product_name"] == "쌀"
        assert data["items"][0]["total_price"] == 500000.0

    def test_create_shipment_insufficient_permission(self, client, db: Session):
        """권한 부족으로 출하 생성 실패 테스트"""
        # 테스트 데이터 준비
        setup = TestDataFactory.create_complete_user_setup(
            db, username="member", role=ProfileRole.member
        )
        member = setup["profile"]
        user = setup["user"]
        from app.core.auth.dependencies import get_current_user
        client.app.dependency_overrides[get_current_user] = lambda: user
        
        # 출하 생성 요청
        shipment_data = {
            "title": "테스트 출하",
            "contract_id": str(uuid4()),
            "shipment_datetime": datetime.now().isoformat(),
            "items": []
        }
        
        # API 호출
        response = client.post(
            "/shipments/",
            json=shipment_data,
            headers={"X-Profile-ID": str(member.id)}
        )
        
        # 검증
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_shipment_success(self, client, db: Session):
        """출하 조회 성공 테스트"""
        # 테스트 데이터 준비
        setup = TestDataFactory.create_complete_user_setup(db, username="viewer")
        viewer = setup["profile"]
        user = setup["user"]
        supplier_company = setup["company"]
        
        buyer_company = CompanyFactory.create_company(db, name="구매 회사")
        
        # 계약 생성
        from app.core.auth.dependencies import get_current_user
        client.app.dependency_overrides[get_current_user] = lambda: user
        contract_data = ContractFactory.create_complete_contract(
            db, supplier_company.id, buyer_company.id, viewer.id
        )
        contract = contract_data["contract"]
        
        # 출하 생성
        shipment_data = ShipmentFactory.create_complete_shipment(
            db, contract.id, viewer.id,
            supplier_company_id=supplier_company.id,
            receiver_company_id=buyer_company.id
        )
        shipment = shipment_data["shipment"]
        
        # API 호출
        response = client.get(
            f"/shipments/{shipment.id}",
            headers={"X-Profile-ID": str(viewer.id)}
        )
        
        # 검증
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(shipment.id)
        assert data["title"] == shipment.title
        assert len(data["items"]) > 0

    def test_get_shipment_not_found(self, client, db: Session):
        """존재하지 않는 출하 조회 테스트"""
        # 테스트 데이터 준비
        setup = TestDataFactory.create_complete_user_setup(db, username="viewer")
        viewer = setup["profile"]
        user = setup["user"]
        from app.core.auth.dependencies import get_current_user
        client.app.dependency_overrides[get_current_user] = lambda: user
        
        # API 호출
        response = client.get(
            f"/shipments/{uuid4()}",
            headers={"X-Profile-ID": str(viewer.id)}
        )
        
        # 검증
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_shipment_no_permission(self, client, db: Session):
        """권한 없는 출하 조회 테스트"""
        # 테스트 데이터 준비
        setup1 = TestDataFactory.create_complete_user_setup(db, username="creator")
        creator = setup1["profile"]
        user1 = setup1["user"]
        supplier_company = setup1["company"]
        
        setup2 = TestDataFactory.create_complete_user_setup(db, username="other", company_name="다른 회사")
        other = setup2["profile"]
        user2 = setup2["user"]
        
        buyer_company = CompanyFactory.create_company(db, name="구매 회사")
        
        # 계약 생성
        from app.core.auth.dependencies import get_current_user
        client.app.dependency_overrides[get_current_user] = lambda: user1
        contract_data = ContractFactory.create_complete_contract(
            db, supplier_company.id, buyer_company.id, creator.id
        )
        contract = contract_data["contract"]
        
        # 출하 생성
        shipment_data = ShipmentFactory.create_complete_shipment(
            db, contract.id, creator.id,
            supplier_company_id=supplier_company.id,
            receiver_company_id=buyer_company.id
        )
        shipment = shipment_data["shipment"]
        
        # 다른 회사 사용자가 조회 시도
        client.app.dependency_overrides[get_current_user] = lambda: user2
        response = client.get(
            f"/shipments/{shipment.id}",
            headers={"X-Profile-ID": str(other.id)}
        )
        
        # 검증
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_shipments_success(self, client, db: Session):
        """출하 목록 조회 성공 테스트"""
        # 테스트 데이터 준비
        setup = TestDataFactory.create_complete_user_setup(db, username="viewer")
        viewer = setup["profile"]
        user = setup["user"]
        supplier_company = setup["company"]
        
        buyer_company = CompanyFactory.create_company(db, name="구매 회사")
        
        # 계약 생성
        from app.core.auth.dependencies import get_current_user
        client.app.dependency_overrides[get_current_user] = lambda: user
        contract_data = ContractFactory.create_complete_contract(
            db, supplier_company.id, buyer_company.id, viewer.id
        )
        contract = contract_data["contract"]
        
        # 여러 출하 생성
        for i in range(3):
            ShipmentFactory.create_complete_shipment(
                db, contract.id, viewer.id,
                title=f"출하 {i+1}",
                supplier_company_id=supplier_company.id,
                receiver_company_id=buyer_company.id
            )
        
        # API 호출
        response = client.get(
            "/shipments/",
            headers={"X-Profile-ID": str(viewer.id)}
        )
        
        # 검증
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["shipments"]) == 3
        assert data["total"] == 3

    def test_list_shipments_with_filters(self, client, db: Session):
        """필터를 사용한 출하 목록 조회 테스트"""
        # 테스트 데이터 준비
        setup = TestDataFactory.create_complete_user_setup(db, username="viewer")
        viewer = setup["profile"]
        user = setup["user"]
        supplier_company = setup["company"]
        
        buyer_company = CompanyFactory.create_company(db, name="구매 회사")
        
        # 계약 생성
        from app.core.auth.dependencies import get_current_user
        client.app.dependency_overrides[get_current_user] = lambda: user
        contract_data = ContractFactory.create_complete_contract(
            db, supplier_company.id, buyer_company.id, viewer.id
        )
        contract = contract_data["contract"]
        
        # 다양한 상태의 출하 생성
        ShipmentFactory.create_shipment(
            db, contract.id, viewer.id,
            title="대기 출하",
            supplier_company_id=supplier_company.id,
            receiver_company_id=buyer_company.id,
            status="pending"
        )
        
        ShipmentFactory.create_shipment(
            db, contract.id, viewer.id,
            title="완료 출하",
            supplier_company_id=supplier_company.id,
            receiver_company_id=buyer_company.id,
            status="delivered"
        )
        
        # 상태별 필터링 테스트
        response = client.get(
            "/shipments/?shipment_status=pending",
            headers={"X-Profile-ID": str(viewer.id)}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["shipments"]) == 1
        assert data["shipments"][0]["title"] == "대기 출하"

    def test_update_shipment_success(self, client, db: Session):
        """출하 업데이트 성공 테스트"""
        # 테스트 데이터 준비
        setup = TestDataFactory.create_complete_user_setup(db, username="updater")
        updater = setup["profile"]
        user = setup["user"]
        supplier_company = setup["company"]
        
        buyer_company = CompanyFactory.create_company(db, name="구매 회사")
        
        # 계약 생성
        from app.core.auth.dependencies import get_current_user
        client.app.dependency_overrides[get_current_user] = lambda: user
        contract_data = ContractFactory.create_complete_contract(
            db, supplier_company.id, buyer_company.id, updater.id
        )
        contract = contract_data["contract"]
        
        # 출하 생성
        shipment_data = ShipmentFactory.create_complete_shipment(
            db, contract.id, updater.id,
            supplier_company_id=supplier_company.id,
            receiver_company_id=buyer_company.id
        )
        shipment = shipment_data["shipment"]
        
        # 업데이트 요청 데이터
        update_data = {
            "title": "업데이트된 출하",
            "contract_id": str(contract.id),
            "shipment_datetime": datetime.now().isoformat(),
            "shipment_status": "ready",
            "items": [
                {
                    "shipment_id": str(uuid4()),
                    "product_name": "업데이트된 쌀",
                    "quality": "B",
                    "quantity": 75,
                    "unit_price": 12000.0,
                    "total_price": 900000.0
                }
            ]
        }
        
        # API 호출
        response = client.put(
            f"/shipments/{shipment.id}",
            json=update_data,
            headers={"X-Profile-ID": str(updater.id)}
        )
        
        # 검증
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "업데이트된 출하"
        assert data["shipment_status"] == "ready"
        assert len(data["items"]) == 1
        assert data["items"][0]["product_name"] == "업데이트된 쌀"
        assert data["items"][0]["total_price"] == 900000.0

    def test_update_shipment_not_found(self, client, db: Session):
        """존재하지 않는 출하 업데이트 테스트"""
        # 테스트 데이터 준비
        setup = TestDataFactory.create_complete_user_setup(db, username="updater")
        updater = setup["profile"]
        user = setup["user"]
        from app.core.auth.dependencies import get_current_user
        client.app.dependency_overrides[get_current_user] = lambda: user
        update_data = {
            "title": "업데이트된 출하",
            "contract_id": str(uuid4()),
            "shipment_datetime": datetime.now().isoformat(),
            "items": []
        }
        
        # API 호출
        response = client.put(
            f"/shipments/{uuid4()}",
            json=update_data,
            headers={"X-Profile-ID": str(updater.id)}
        )
        
        # 검증
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_shipment_success(self, client, db: Session):
        """출하 삭제 성공 테스트"""
        # 테스트 데이터 준비
        setup = TestDataFactory.create_complete_user_setup(db, username="deleter")
        deleter = setup["profile"]
        user = setup["user"]
        supplier_company = setup["company"]
        
        buyer_company = CompanyFactory.create_company(db, name="구매 회사")
        
        # 계약 생성
        from app.core.auth.dependencies import get_current_user
        client.app.dependency_overrides[get_current_user] = lambda: user
        contract_data = ContractFactory.create_complete_contract(
            db, supplier_company.id, buyer_company.id, deleter.id
        )
        contract = contract_data["contract"]
        
        # 출하 생성
        shipment_data = ShipmentFactory.create_complete_shipment(
            db, contract.id, deleter.id,
            supplier_company_id=supplier_company.id,
            receiver_company_id=buyer_company.id
        )
        shipment = shipment_data["shipment"]
        
        # API 호출
        response = client.delete(
            f"/shipments/{shipment.id}",
            headers={"X-Profile-ID": str(deleter.id)}
        )
        
        # 검증
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # 삭제 확인
        get_response = client.get(
            f"/shipments/{shipment.id}",
            headers={"X-Profile-ID": str(deleter.id)}
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_shipment_not_found(self, client, db: Session):
        """존재하지 않는 출하 삭제 테스트"""
        # 테스트 데이터 준비
        setup = TestDataFactory.create_complete_user_setup(db, username="deleter")
        deleter = setup["profile"]
        user = setup["user"]
        from app.core.auth.dependencies import get_current_user
        client.app.dependency_overrides[get_current_user] = lambda: user
        
        # API 호출
        response = client.delete(
            f"/shipments/{uuid4()}",
            headers={"X-Profile-ID": str(deleter.id)}
        )
        
        # 검증
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_shipment_with_center_information(self, client, db: Session):
        """센터 정보가 포함된 출하 테스트"""
        # 테스트 데이터 준비
        setup = TestDataFactory.create_complete_user_setup(db, username="creator")
        creator = setup["profile"]
        user = setup["user"]
        supplier_company = setup["company"]
        
        buyer_company = CompanyFactory.create_company(db, name="구매 회사")
        
        # 센터 생성
        from app.core.auth.dependencies import get_current_user
        client.app.dependency_overrides[get_current_user] = lambda: user
        departure_center = CenterFactory.create_center(
            db, supplier_company.id, "출발 센터"
        )
        arrival_center = CenterFactory.create_center(
            db, buyer_company.id, "도착 센터"
        )
        
        # 계약 생성
        contract_data = ContractFactory.create_complete_contract(
            db, supplier_company.id, buyer_company.id, creator.id
        )
        contract = contract_data["contract"]
        
        # 센터 정보가 포함된 출하 생성
        shipment_data = {
            "title": "센터 출하",
            "contract_id": str(contract.id),
            "supplier_company_id": str(supplier_company.id),
            "receiver_company_id": str(buyer_company.id),
            "departure_center_id": str(departure_center.id),
            "arrival_center_id": str(arrival_center.id),
            "shipment_datetime": datetime.now().isoformat(),
            "shipment_status": "pending",
            "items": [
                {
                    "shipment_id": str(uuid4()),
                    "product_name": "센터 쌀",
                    "quality": "A",
                    "quantity": 100,
                    "unit_price": 15000.0,
                    "total_price": 1500000.0
                }
            ]
        }
        
        # API 호출
        response = client.post(
            "/shipments/",
            json=shipment_data,
            headers={"X-Profile-ID": str(creator.id)}
        )
        
        # 검증
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["departure_center_id"] == str(departure_center.id)
        assert data["arrival_center_id"] == str(arrival_center.id)

    def test_shipment_pagination(self, client, db: Session):
        """출하 목록 페이지네이션 테스트"""
        # 테스트 데이터 준비
        setup = TestDataFactory.create_complete_user_setup(db, username="viewer")
        viewer = setup["profile"]
        user = setup["user"]
        supplier_company = setup["company"]
        
        buyer_company = CompanyFactory.create_company(db, name="구매 회사")
        
        # 계약 생성
        from app.core.auth.dependencies import get_current_user
        client.app.dependency_overrides[get_current_user] = lambda: user
        contract_data = ContractFactory.create_complete_contract(
            db, supplier_company.id, buyer_company.id, viewer.id
        )
        contract = contract_data["contract"]
        
        # 5개의 출하 생성
        for i in range(5):
            ShipmentFactory.create_complete_shipment(
                db, contract.id, viewer.id,
                title=f"출하 {i+1}",
                supplier_company_id=supplier_company.id,
                receiver_company_id=buyer_company.id
            )
        
        # 페이지네이션 테스트 (limit=2, skip=1)
        response = client.get(
            "/shipments/?limit=2&skip=1",
            headers={"X-Profile-ID": str(viewer.id)}
        )
        
        # 검증
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["shipments"]) == 2
        assert data["total"] == 5 