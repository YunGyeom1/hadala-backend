import pytest
from datetime import datetime, timedelta, date, time
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from tests.factories import (
    UserFactory, ProfileFactory, CompanyFactory, CenterFactory, ContractFactory
)
from app.core.auth.utils import create_access_token
from app.profile.models import ProfileType, ProfileRole
from app.transactions.common.models import ContractStatus, PaymentStatus, ProductQuality
import uuid

@pytest.fixture
def company_token_and_profile(db: Session):
    """회사 소유자 토큰과 프로필을 생성합니다."""
    user = UserFactory.create_user(db)
    profile = ProfileFactory.create_wholesaler_profile(
        db, user_id=user.id, username=f"company_owner_{uuid.uuid4().hex[:8]}"
    )
    token = create_access_token({"sub": str(user.id)})
    return token, profile

@pytest.fixture
def supplier_company(db: Session, company_token_and_profile):
    """공급자 회사를 생성합니다."""
    token, profile = company_token_and_profile
    company = CompanyFactory.create_wholesale_company(
        db, owner_id=profile.id, name=f"공급자 회사_{uuid.uuid4().hex[:8]}"
    )
    
    # 프로필의 company_id를 설정
    profile.company_id = company.id
    db.commit()
    db.refresh(profile)
    
    return company

@pytest.fixture
def receiver_company(db: Session):
    """수신자 회사를 생성합니다."""
    user = UserFactory.create_user(db)
    profile = ProfileFactory.create_retailer_profile(
        db, user_id=user.id, username=f"receiver_{uuid.uuid4().hex[:8]}"
    )
    company = CompanyFactory.create_retail_company(
        db, owner_id=profile.id, name=f"수신자 회사_{uuid.uuid4().hex[:8]}"
    )
    
    # 프로필의 company_id를 설정
    profile.company_id = company.id
    db.commit()
    db.refresh(profile)
    
    return company

@pytest.fixture
def farmer_company(db: Session):
    """농민 회사를 생성합니다."""
    user = UserFactory.create_user(db)
    profile = ProfileFactory.create_farmer_profile(
        db, user_id=user.id, username=f"farmer_{uuid.uuid4().hex[:8]}"
    )
    company = CompanyFactory.create_farmer_company(
        db, owner_id=profile.id, name=f"농민 회사_{uuid.uuid4().hex[:8]}"
    )
    
    # 프로필의 company_id를 설정
    profile.company_id = company.id
    db.commit()
    db.refresh(profile)
    
    return company

@pytest.fixture
def test_contracts(db: Session, supplier_company, receiver_company, farmer_company, company_token_and_profile):
    token, profile = company_token_and_profile
    today = date.today()
    
    # 1. 미수금 계약 (우리가 공급자, 미결제)
    contract1 = ContractFactory.create_contract(
        db,
        supplier_company_id=supplier_company.id,
        receiver_company_id=receiver_company.id,
        title="공급 계약 A",
        total_amount=2000000,
        payment_status=PaymentStatus.UNPAID,
        contract_date=datetime.combine(today, time.min),
        payment_due_date=datetime.combine(today + timedelta(days=30), time.min),
        creator_id=profile.id
    )
    
    # 2. 미수금 계약 (우리가 수신자, 미결제)
    contract2 = ContractFactory.create_contract(
        db,
        supplier_company_id=farmer_company.id,
        receiver_company_id=supplier_company.id,
        title="구매 계약 B",
        total_amount=1500000,
        payment_status=PaymentStatus.UNPAID,
        contract_date=datetime.combine(today, time.min),
        payment_due_date=datetime.combine(today + timedelta(days=15), time.min),
        creator_id=profile.id
    )
    
    # 3. 완료된 계약 (우리가 공급자, 결제 완료)
    contract3 = ContractFactory.create_contract(
        db,
        supplier_company_id=supplier_company.id,
        receiver_company_id=receiver_company.id,
        title="완료된 계약 C",
        total_amount=3000000,
        payment_status=PaymentStatus.PAID,
        contract_date=datetime.combine(today - timedelta(days=60), time.min),
        payment_due_date=datetime.combine(today - timedelta(days=30), time.min),
        creator_id=profile.id
    )
    
    # 4. 연체 계약 (우리가 수신자, 연체) - 지출 계약이어야 연체로 판정됨
    contract4 = ContractFactory.create_contract(
        db,
        supplier_company_id=farmer_company.id,
        receiver_company_id=supplier_company.id,
        title="연체 계약 D",
        total_amount=500000,
        payment_status=PaymentStatus.UNPAID,
        contract_date=datetime.combine(today - timedelta(days=45), time.min),
        payment_due_date=datetime.combine(today - timedelta(days=15), time.min),
        creator_id=profile.id
    )
    
    return {
        "unpaid_supplier": contract1,
        "unpaid_receiver": contract2,
        "paid_contract": contract3,
        "overdue_contract": contract4
    }

def auth_headers(token, profile_id):
    """인증 헤더를 생성합니다."""
    return {"Authorization": f"Bearer {token}", "X-Profile-ID": str(profile_id)}

class TestPaymentAPI:
    """Payment API 테스트"""
    
    def test_get_payment_report_success(
        self, client: TestClient, db: Session,
        company_token_and_profile, supplier_company, test_contracts
    ):
        """지급 현황 보고서 조회 성공 테스트"""
        token, profile = company_token_and_profile
        
        response = client.get(
            "/payments/report",
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 요약 정보 확인
        assert "summary" in result
        assert "contracts" in result
        
        summary = result["summary"]
        # supplier_company가 공급자인 계약: 2000000 + 3000000 = 5000000 (완료된 계약은 제외)
        # supplier_company가 수신자인 계약: 1500000 + 500000 = 2000000
        assert summary["unpaid_receivables"] == 2000000.0  # 미결제 공급 계약: 2000000
        assert summary["overdue_payables"] == 500000.0     # 연체된 구매 계약: 500000
        assert summary["prepaid_income"] == 0.0            # 선수금 없음
        assert summary["prepaid_expense"] == 0.0           # 선지급 없음
        
        # 계약 목록 확인
        contracts = result["contracts"]
        assert len(contracts) == 4
        
        # 특정 계약 확인
        contract_a = next(c for c in contracts if c["contract_name"] == "공급 계약 A")
        assert contract_a["income"] == 2000000.0
        assert contract_a["expense"] == 0.0
        assert contract_a["status"] == "unpaid"
        assert contract_a["pending_amount"] == 2000000.0
        assert contract_a["is_overdue"] == False
        
        contract_d = next(c for c in contracts if c["contract_name"] == "연체 계약 D")
        assert contract_d["income"] == 0.0
        assert contract_d["expense"] == 500000.0
        assert contract_d["status"] == "unpaid"
        assert contract_d["pending_amount"] == 500000.0
        assert contract_d["is_overdue"] == True

    def test_get_payment_report_with_date_filter(
        self, client: TestClient, db: Session,
        company_token_and_profile, supplier_company, test_contracts
    ):
        """날짜 필터가 적용된 지급 현황 보고서 조회 테스트"""
        token, profile = company_token_and_profile
        
        # 오늘 날짜만 필터링
        today = date.today()
        response = client.get(
            f"/payments/report?start_date={today}&end_date={today}",
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 오늘 생성된 계약만 포함되어야 함 (contract3, contract4 제외)
        contracts = result["contracts"]
        assert len(contracts) == 2  # contract1, contract2만 오늘 생성
        
        # 연체된 계약이 제외되었는지 확인
        overdue_contracts = [c for c in contracts if c["is_overdue"]]
        assert len(overdue_contracts) == 0

    def test_get_payment_summary_success(
        self, client: TestClient, db: Session,
        company_token_and_profile, supplier_company, test_contracts
    ):
        """지급 현황 요약 조회 성공 테스트"""
        token, profile = company_token_and_profile
        
        response = client.get(
            "/payments/summary",
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 요약 정보만 반환되는지 확인
        assert "unpaid_receivables" in result
        assert "overdue_payables" in result
        assert "prepaid_income" in result
        assert "prepaid_expense" in result
        assert "contracts" not in result  # 계약 목록은 포함되지 않아야 함
        
        assert result["unpaid_receivables"] == 2000000.0
        assert result["overdue_payables"] == 500000.0
        assert result["prepaid_income"] == 0.0
        assert result["prepaid_expense"] == 0.0

    def test_get_payment_summary_with_date_filter(
        self, client: TestClient, db: Session,
        company_token_and_profile, supplier_company, test_contracts
    ):
        """날짜 필터가 적용된 지급 현황 요약 조회 테스트"""
        token, profile = company_token_and_profile
        
        # 오늘 날짜만 필터링
        today = date.today()
        response = client.get(
            f"/payments/summary?start_date={today}&end_date={today}",
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 연체된 계약이 제외되었으므로 overdue_payables가 0이어야 함
        assert result["overdue_payables"] == 0.0

    def test_get_overdue_contracts_success(
        self, client: TestClient, db: Session,
        company_token_and_profile, supplier_company, test_contracts
    ):
        """연체 계약 목록 조회 성공 테스트"""
        token, profile = company_token_and_profile
        
        response = client.get(
            "/payments/overdue",
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 연체된 계약만 반환되는지 확인
        overdue_contracts = result["overdue_contracts"]
        assert len(overdue_contracts) == 1  # 연체 계약 D만 연체
        
        overdue_contract = overdue_contracts[0]
        assert overdue_contract["title"] == "연체 계약 D"
        assert overdue_contract["total_price"] == 500000.0
        assert overdue_contract["days_overdue"] > 0  # 연체일수는 양수여야 함

    def test_payment_report_no_company(
        self, client: TestClient, db: Session
    ):
        """회사에 속하지 않은 사용자의 지급 현황 조회 시 400 오류"""
        user = UserFactory.create_user(db)
        profile = ProfileFactory.create_wholesaler_profile(
            db, user_id=user.id, username=f"no_company_{uuid.uuid4().hex[:8]}"
        )
        token = create_access_token({"sub": str(user.id)})
        
        response = client.get(
            "/payments/report",
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 400
        assert "회사에 속해있지 않습니다" in response.json()["detail"]

    def test_payment_summary_no_company(
        self, client: TestClient, db: Session
    ):
        """회사에 속하지 않은 사용자의 지급 현황 요약 조회 시 400 오류"""
        user = UserFactory.create_user(db)
        profile = ProfileFactory.create_wholesaler_profile(
            db, user_id=user.id, username=f"no_company_{uuid.uuid4().hex[:8]}"
        )
        token = create_access_token({"sub": str(user.id)})
        
        response = client.get(
            "/payments/summary",
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 400
        assert "회사에 속해있지 않습니다" in response.json()["detail"]

    def test_overdue_contracts_no_company(
        self, client: TestClient, db: Session
    ):
        """회사에 속하지 않은 사용자의 연체 계약 조회 시 400 오류"""
        user = UserFactory.create_user(db)
        profile = ProfileFactory.create_wholesaler_profile(
            db, user_id=user.id, username=f"no_company_{uuid.uuid4().hex[:8]}"
        )
        token = create_access_token({"sub": str(user.id)})
        
        response = client.get(
            "/payments/overdue",
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 400
        assert "회사에 속해있지 않습니다" in response.json()["detail"]

    def test_payment_report_unauthorized(
        self, client: TestClient, db: Session
    ):
        """인증되지 않은 사용자의 지급 현황 조회 시 401 오류"""
        response = client.get("/payments/report")
        assert response.status_code == 401

    def test_payment_summary_unauthorized(
        self, client: TestClient, db: Session
    ):
        """인증되지 않은 사용자의 지급 현황 요약 조회 시 401 오류"""
        response = client.get("/payments/summary")
        assert response.status_code == 401

    def test_overdue_contracts_unauthorized(
        self, client: TestClient, db: Session
    ):
        """인증되지 않은 사용자의 연체 계약 조회 시 401 오류"""
        response = client.get("/payments/overdue")
        assert response.status_code == 401

    def test_payment_report_empty_result(
        self, client: TestClient, db: Session,
        company_token_and_profile, supplier_company
    ):
        """계약이 없는 경우의 지급 현황 조회 테스트"""
        token, profile = company_token_and_profile
        
        response = client.get(
            "/payments/report",
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 모든 값이 0이어야 함
        summary = result["summary"]
        assert summary["unpaid_receivables"] == 0.0
        assert summary["overdue_payables"] == 0.0
        assert summary["prepaid_income"] == 0.0
        assert summary["prepaid_expense"] == 0.0
        
        # 계약 목록이 비어있어야 함
        assert len(result["contracts"]) == 0 