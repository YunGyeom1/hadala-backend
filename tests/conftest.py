import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from uuid import uuid4
import uuid

from app.database import Base, get_db
from app.main import app
from app.core.auth.utils import create_access_token
from app.user.models import User
from app.farmer.models import Farmer
from app.retailer.models import Retailer
from app.company.models import Company
from app.wholesaler.models import Wholesaler

# SQLite 인메모리 DB 설정
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_user(db: Session):
    user = User(
        email=f"test{uuid.uuid4()}@example.com",
        name="Test User",
        oauth_provider="google",
        oauth_sub=str(uuid.uuid4())
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="function")
def other_user(db: Session):
    user = User(
        email=f"other{uuid.uuid4()}@example.com",
        name="Other User",
        oauth_provider="google",
        oauth_sub=str(uuid.uuid4())
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_wholesaler(db, test_user):
    wholesaler = Wholesaler(user_id=test_user.id, role="owner")
    db.add(wholesaler)
    db.commit()
    db.refresh(wholesaler)
    return wholesaler

@pytest.fixture(scope="function")
def other_wholesaler(db: Session, other_user: User):
    wholesaler = Wholesaler(
        user_id=other_user.id,
        name="다른 도매상",
        phone="010-9876-5432",
        role="staff"
    )
    db.add(wholesaler)
    db.commit()
    db.refresh(wholesaler)
    return wholesaler

@pytest.fixture
def test_company(db, test_wholesaler):
    company = Company(
        name="테스트 회사",
        description="테스트 회사 설명",
        business_number=str(uuid.uuid4()),
        address="서울시 강남구",
        phone="02-1234-5678",
        email=f"test{uuid.uuid4()}@company.com",
        owner=test_wholesaler.user_id
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    # 도매상의 회사 ID 업데이트
    test_wholesaler.company_id = company.id
    db.commit()
    return company

@pytest.fixture
def wholesaler_token_headers(test_user):
    token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def other_wholesaler_token_headers(other_user):
    access_token = create_access_token({"sub": str(other_user.id)})
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def fake_user_id():
    return str(uuid4())

@pytest.fixture
def test_farmer(db: Session, test_user: User):
    farmer = Farmer(
        name="테스트농부",
        address="경기도 남양주시",
        farm_size_m2=1200.0,
        annual_output_kg=2000.0,
        farm_members=4,
        user_id=test_user.id
    )
    db.add(farmer)
    db.commit()
    db.refresh(farmer)
    return farmer

@pytest.fixture
def test_retailer(db: Session, test_user: User):
    retailer = Retailer(
        name="테스트마트",
        address="서울시 강남구",
        description="신선식품 전문 마트",
        user_id=test_user.id
    )
    db.add(retailer)
    db.commit()
    db.refresh(retailer)
    return retailer