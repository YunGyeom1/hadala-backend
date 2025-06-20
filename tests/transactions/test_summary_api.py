import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4
from fastapi import status
from sqlalchemy.orm import Session

from tests.factories import (
    ProfileFactory, CompanyFactory, CenterFactory, 
    ContractFactory, ShipmentFactory, TestDataFactory
)
from app.profile.models import ProfileRole
from app.transactions.common.models import ShipmentStatus, ProductQuality, ContractStatus
from app.transactions.summary.schemas import TransactionType, Direction


class TestSummaryAPI:
    """Summary API 테스트 클래스"""

    def test_get_daily_summary_by_request_contract_outbound(self, client, db: Session):
        """계약 출고 일별 요약 테스트"""
        # 테스트 데이터 준비
        setup = TestDataFactory.create_complete_user_setup(db, username="viewer")
        viewer = setup["profile"]
        user = setup["user"]
        supplier_company = setup["company"]
        
        buyer_company = CompanyFactory.create_company(db, name="구매 회사")
        
        # 센터 생성
        departure_center = CenterFactory.create_center(
            db, supplier_company.id, "출발 센터"
        )
        arrival_center = CenterFactory.create_center(
            db, buyer_company.id, "도착 센터"
        )
        
        # 계약 생성
        from app.core.auth.dependencies import get_current_user
        client.app.dependency_overrides[get_current_user] = lambda: user
        
        contract_data = ContractFactory.create_complete_contract(
            db, supplier_company.id, buyer_company.id, viewer.id,
            contract_date=datetime.now(),
            delivery_datetime=datetime.now()
        )
        contract = contract_data["contract"]
        
        # 계약에 센터 정보 추가
        contract.departure_center_id = departure_center.id
        contract.arrival_center_id = arrival_center.id
        db.commit()
        
        # 요약 요청 데이터
        today = date.today()
        summary_request = {
            "start_date": today.isoformat(),
            "end_date": today.isoformat(),
            "direction": "outbound",
            "transaction_type": "contract"
        }
        
        # API 호출
        response = client.post(
            "/summary/daily-summary",
            json=summary_request,
            headers={"X-Profile-ID": str(viewer.id)}
        )
        
        # 응답 내용 출력
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.json()}")
        
        # 검증
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["direction"] == "outbound"
        assert data["transaction_type"] == "contract"
        assert len(data["daily_summaries"]) > 0

    def test_get_daily_summary_by_request_shipment_inbound(self, client, db: Session):
        """출하 입고 일별 요약 테스트"""
        # 테스트 데이터 준비
        setup = TestDataFactory.create_complete_user_setup(db, username="viewer")
        viewer = setup["profile"]
        user = setup["user"]
        supplier_company = setup["company"]
        
        buyer_company = CompanyFactory.create_company(db, name="구매 회사")
        
        # 센터 생성
        departure_center = CenterFactory.create_center(
            db, supplier_company.id, "출발 센터"
        )
        arrival_center = CenterFactory.create_center(
            db, buyer_company.id, "도착 센터"
        )
        
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
            receiver_company_id=buyer_company.id,
            departure_center_id=departure_center.id,
            arrival_center_id=arrival_center.id,
            shipment_datetime=datetime.now()
        )
        
        # 요약 요청 데이터
        today = date.today()
        summary_request = {
            "start_date": today.isoformat(),
            "end_date": today.isoformat(),
            "direction": "inbound",
            "transaction_type": "shipment"
        }
        
        # API 호출
        response = client.post(
            "/summary/daily-summary",
            json=summary_request,
            headers={"X-Profile-ID": str(viewer.id)}
        )
        
        # 검증
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["direction"] == "inbound"
        assert data["transaction_type"] == "shipment"

    def test_get_contract_outbound_summary(self, client, db: Session):
        """계약 출고 요약 GET 엔드포인트 테스트"""
        # 테스트 데이터 준비
        setup = TestDataFactory.create_complete_user_setup(db, username="viewer")
        viewer = setup["profile"]
        user = setup["user"]
        supplier_company = setup["company"]
        
        buyer_company = CompanyFactory.create_company(db, name="구매 회사")
        
        # 센터 생성
        departure_center = CenterFactory.create_center(
            db, supplier_company.id, "출발 센터"
        )
        arrival_center = CenterFactory.create_center(
            db, buyer_company.id, "도착 센터"
        )
        
        # 계약 생성
        from app.core.auth.dependencies import get_current_user
        client.app.dependency_overrides[get_current_user] = lambda: user
        
        contract_data = ContractFactory.create_complete_contract(
            db, supplier_company.id, buyer_company.id, viewer.id,
            contract_date=datetime.now(),
            delivery_datetime=datetime.now()
        )
        contract = contract_data["contract"]
        
        # 계약에 센터 정보 추가
        contract.departure_center_id = departure_center.id
        contract.arrival_center_id = arrival_center.id
        db.commit()
        
        # API 호출
        today = date.today()
        response = client.get(
            f"/summary/contracts/outbound?start_date={today.isoformat()}&end_date={today.isoformat()}",
            headers={"X-Profile-ID": str(viewer.id)}
        )
        
        # 검증
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["direction"] == "outbound"
        assert data["transaction_type"] == "contract"

    def test_get_contract_inbound_summary(self, client, db: Session):
        """계약 입고 요약 GET 엔드포인트 테스트"""
        # 테스트 데이터 준비
        setup = TestDataFactory.create_complete_user_setup(db, username="viewer")
        viewer = setup["profile"]
        user = setup["user"]
        supplier_company = setup["company"]
        
        buyer_company = CompanyFactory.create_company(db, name="구매 회사")
        
        # 센터 생성
        departure_center = CenterFactory.create_center(
            db, supplier_company.id, "출발 센터"
        )
        arrival_center = CenterFactory.create_center(
            db, buyer_company.id, "도착 센터"
        )
        
        # 계약 생성
        from app.core.auth.dependencies import get_current_user
        client.app.dependency_overrides[get_current_user] = lambda: user
        
        contract_data = ContractFactory.create_complete_contract(
            db, supplier_company.id, buyer_company.id, viewer.id,
            contract_date=datetime.now(),
            delivery_datetime=datetime.now()
        )
        contract = contract_data["contract"]
        
        # 계약에 센터 정보 추가
        contract.departure_center_id = departure_center.id
        contract.arrival_center_id = arrival_center.id
        db.commit()
        
        # API 호출
        today = date.today()
        response = client.get(
            f"/summary/contracts/inbound?start_date={today.isoformat()}&end_date={today.isoformat()}",
            headers={"X-Profile-ID": str(viewer.id)}
        )
        
        # 검증
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["direction"] == "inbound"
        assert data["transaction_type"] == "contract"

    def test_get_shipment_outbound_summary(self, client, db: Session):
        """출하 출고 요약 GET 엔드포인트 테스트"""
        # 테스트 데이터 준비
        setup = TestDataFactory.create_complete_user_setup(db, username="viewer")
        viewer = setup["profile"]
        user = setup["user"]
        supplier_company = setup["company"]
        
        buyer_company = CompanyFactory.create_company(db, name="구매 회사")
        
        # 센터 생성
        departure_center = CenterFactory.create_center(
            db, supplier_company.id, "출발 센터"
        )
        arrival_center = CenterFactory.create_center(
            db, buyer_company.id, "도착 센터"
        )
        
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
            receiver_company_id=buyer_company.id,
            departure_center_id=departure_center.id,
            arrival_center_id=arrival_center.id,
            shipment_datetime=datetime.now()
        )
        
        # API 호출
        today = date.today()
        response = client.get(
            f"/summary/shipments/outbound?start_date={today.isoformat()}&end_date={today.isoformat()}",
            headers={"X-Profile-ID": str(viewer.id)}
        )
        
        # 검증
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["direction"] == "outbound"
        assert data["transaction_type"] == "shipment"

    def test_get_shipment_inbound_summary(self, client, db: Session):
        """출하 입고 요약 GET 엔드포인트 테스트"""
        # 테스트 데이터 준비
        setup = TestDataFactory.create_complete_user_setup(db, username="viewer")
        viewer = setup["profile"]
        user = setup["user"]
        supplier_company = setup["company"]
        
        buyer_company = CompanyFactory.create_company(db, name="구매 회사")
        
        # 센터 생성
        departure_center = CenterFactory.create_center(
            db, supplier_company.id, "출발 센터"
        )
        arrival_center = CenterFactory.create_center(
            db, buyer_company.id, "도착 센터"
        )
        
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
            receiver_company_id=buyer_company.id,
            departure_center_id=departure_center.id,
            arrival_center_id=arrival_center.id,
            shipment_datetime=datetime.now()
        )
        
        # API 호출
        today = date.today()
        response = client.get(
            f"/summary/shipments/inbound?start_date={today.isoformat()}&end_date={today.isoformat()}",
            headers={"X-Profile-ID": str(viewer.id)}
        )
        
        # 검증
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["direction"] == "inbound"
        assert data["transaction_type"] == "shipment"

    def test_summary_date_range(self, client, db: Session):
        """날짜 범위 요약 테스트"""
        # 테스트 데이터 준비
        setup = TestDataFactory.create_complete_user_setup(db, username="viewer")
        viewer = setup["profile"]
        user = setup["user"]
        supplier_company = setup["company"]
        
        buyer_company = CompanyFactory.create_company(db, name="구매 회사")
        
        # 센터 생성
        departure_center = CenterFactory.create_center(
            db, supplier_company.id, "출발 센터"
        )
        arrival_center = CenterFactory.create_center(
            db, buyer_company.id, "도착 센터"
        )
        
        # 계약 생성
        from app.core.auth.dependencies import get_current_user
        client.app.dependency_overrides[get_current_user] = lambda: user
        
        # 여러 날짜에 걸친 계약 생성
        start_date = date.today() - timedelta(days=2)
        end_date = date.today()
        
        for i in range(3):
            contract_date = start_date + timedelta(days=i)
            contract_data = ContractFactory.create_complete_contract(
                db, supplier_company.id, buyer_company.id, viewer.id,
                contract_date=datetime.combine(contract_date, datetime.min.time()),
                delivery_datetime=datetime.combine(contract_date, datetime.min.time())
            )
            contract = contract_data["contract"]
            
            # 계약에 센터 정보 추가
            contract.departure_center_id = departure_center.id
            contract.arrival_center_id = arrival_center.id
            db.commit()
        
        # 요약 요청 데이터
        summary_request = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "direction": "outbound",
            "transaction_type": "contract"
        }
        
        # API 호출
        response = client.post(
            "/summary/daily-summary",
            json=summary_request,
            headers={"X-Profile-ID": str(viewer.id)}
        )
        
        # 검증
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["daily_summaries"]) > 0
        assert data["start_date"] == start_date.isoformat()
        assert data["end_date"] == end_date.isoformat()

    def test_summary_empty_result(self, client, db: Session):
        """데이터가 없는 경우 요약 테스트"""
        # 테스트 데이터 준비
        setup = TestDataFactory.create_complete_user_setup(db, username="viewer")
        viewer = setup["profile"]
        user = setup["user"]
        
        from app.core.auth.dependencies import get_current_user
        client.app.dependency_overrides[get_current_user] = lambda: user
        
        # 과거 날짜로 요약 요청 (데이터가 없을 확률이 높음)
        past_date = date.today() - timedelta(days=365)
        summary_request = {
            "start_date": past_date.isoformat(),
            "end_date": past_date.isoformat(),
            "direction": "outbound",
            "transaction_type": "contract"
        }
        
        # API 호출
        response = client.post(
            "/summary/daily-summary",
            json=summary_request,
            headers={"X-Profile-ID": str(viewer.id)}
        )
        
        # 검증
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["direction"] == "outbound"
        assert data["transaction_type"] == "contract"
        # 데이터가 없으면 daily_summaries가 빈 배열이거나 None일 수 있음

    def test_summary_invalid_date_range(self, client, db: Session):
        """잘못된 날짜 범위 테스트"""
        # 테스트 데이터 준비
        setup = TestDataFactory.create_complete_user_setup(db, username="viewer")
        viewer = setup["profile"]
        user = setup["user"]
        
        from app.core.auth.dependencies import get_current_user
        client.app.dependency_overrides[get_current_user] = lambda: user
        
        # 시작일이 종료일보다 늦은 경우
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        summary_request = {
            "start_date": tomorrow.isoformat(),
            "end_date": today.isoformat(),
            "direction": "outbound",
            "transaction_type": "contract"
        }
        
        # API 호출
        response = client.post(
            "/summary/daily-summary",
            json=summary_request,
            headers={"X-Profile-ID": str(viewer.id)}
        )
        
        # 검증 (날짜 범위가 잘못되어도 API는 동작하지만 빈 결과를 반환)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["direction"] == "outbound"
        assert data["transaction_type"] == "contract"

    def test_summary_multiple_centers(self, client, db: Session):
        """여러 센터 요약 테스트"""
        # 테스트 데이터 준비
        setup = TestDataFactory.create_complete_user_setup(db, username="viewer")
        viewer = setup["profile"]
        user = setup["user"]
        supplier_company = setup["company"]
        
        buyer_company = CompanyFactory.create_company(db, name="구매 회사")
        
        # 여러 센터 생성
        center1 = CenterFactory.create_center(db, supplier_company.id, "센터 1")
        center2 = CenterFactory.create_center(db, supplier_company.id, "센터 2")
        arrival_center = CenterFactory.create_center(db, buyer_company.id, "도착 센터")
        
        # 계약 생성
        from app.core.auth.dependencies import get_current_user
        client.app.dependency_overrides[get_current_user] = lambda: user
        
        # 센터 1에서 출발하는 계약
        contract1_data = ContractFactory.create_complete_contract(
            db, supplier_company.id, buyer_company.id, viewer.id,
            contract_date=datetime.now(),
            delivery_datetime=datetime.now()
        )
        contract1 = contract1_data["contract"]
        contract1.departure_center_id = center1.id
        contract1.arrival_center_id = arrival_center.id
        
        # 센터 2에서 출발하는 계약
        contract2_data = ContractFactory.create_complete_contract(
            db, supplier_company.id, buyer_company.id, viewer.id,
            contract_date=datetime.now(),
            delivery_datetime=datetime.now()
        )
        contract2 = contract2_data["contract"]
        contract2.departure_center_id = center2.id
        contract2.arrival_center_id = arrival_center.id
        
        db.commit()
        
        # 요약 요청 데이터
        today = date.today()
        summary_request = {
            "start_date": today.isoformat(),
            "end_date": today.isoformat(),
            "direction": "outbound",
            "transaction_type": "contract"
        }
        
        # API 호출
        response = client.post(
            "/summary/daily-summary",
            json=summary_request,
            headers={"X-Profile-ID": str(viewer.id)}
        )
        
        # 검증
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["daily_summaries"]) > 0
        
        # 여러 센터의 데이터가 포함되어 있는지 확인
        daily_summary = data["daily_summaries"][0]
        assert len(daily_summary["center_summaries"]) > 0 