import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from uuid import uuid4
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.core.auth.utils import create_access_token
from app.user.models import User
from app.farmer.models import Farmer
from app.retailer.models import Retailer

# SQLite 인메모리 DB 설정
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# DB 세션 및 의존성 오버라이드
@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db):
    user = User(
        id=uuid4(),
        email="test@example.com",
        name="Test User"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def fake_user_id():
    return str(uuid4())

@pytest.fixture
def auth_headers(test_user):
    access_token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def test_user(db: Session):
    user = User(
        email="test@example.com",
        name="Test User",
        oauth_provider="google",
        oauth_sub="testsub"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


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