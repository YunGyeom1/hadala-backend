import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from dotenv import load_dotenv

from app.database.base import Base
from app.database.session import get_db
from app.main import app

# 테스트용 .env.test 파일 로드
load_dotenv(".env.test")

# 테스트용 SQLite 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    """테스트용 데이터베이스 세션을 제공합니다."""
    # 테스트 시작 전 테이블 생성
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # 테스트 종료 후 테이블 삭제
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    """테스트용 FastAPI 클라이언트를 제공합니다."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
