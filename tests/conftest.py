import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database.base import Base
from app.database.session import get_db
import sys
import types
from app.user.models import User

# 테스트용 데이터베이스 URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# 테스트용 엔진 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    # 테스트 데이터베이스 전체 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    # 테스트용 세션 생성
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # 테스트 후 테이블 전체 삭제
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def mock_google_id_token(monkeypatch):
    """google.oauth2.id_token.verify_oauth2_token을 항상 성공하도록 mock 처리"""
    import google.oauth2.id_token
    import google.auth.transport.requests
    
    def fake_verify_oauth2_token(id_token, request, client_id):
        return {
            "sub": "test-google-sub",
            "email": "testuser@example.com",
            "name": "Test User"
        }
    monkeypatch.setattr(google.oauth2.id_token, "verify_oauth2_token", fake_verify_oauth2_token) 