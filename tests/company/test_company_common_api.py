import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.auth.utils import create_access_token
from app.profile.models import ProfileRole, ProfileType
from app.company.common.models import CompanyType
from tests.factories import UserFactory, ProfileFactory, CompanyFactory
import uuid
from app.profile.dependencies import get_current_profile

@pytest.fixture
def owner_token_and_profile(db: Session):
    user = UserFactory.create_user(db)
    profile = ProfileFactory.create_profile(
        db, 
        user_id=user.id, 
        type=ProfileType.wholesaler, 
        role=ProfileRole.owner,
        username=f"owner_{uuid.uuid4().hex[:8]}"
    )
    token = create_access_token({"sub": str(user.id)})
    return token, profile

@pytest.fixture
def company(db: Session, owner_token_and_profile):
    _, profile = owner_token_and_profile
    company = CompanyFactory.create_company(
        db, 
        name="테스트회사", 
        type=CompanyType.wholesaler, 
        owner_id=profile.id  # profile.user_id가 아닌 profile.id로 수정
    )
    profile.company_id = company.id
    db.commit()
    return company

def auth_headers(token, profile_id):
    return {
        "Authorization": f"Bearer {token}",
        "X-Profile-ID": str(profile_id)
    }

def test_create_company(client: TestClient, db: Session, owner_token_and_profile):
    token, profile = owner_token_and_profile
    data = {"name": "새회사", "type": "wholesaler"}
    response = client.post("/companies/create", json=data, headers=auth_headers(token, profile.id))
    assert response.status_code == 200
    assert response.json()["name"] == "새회사"

def test_create_company_duplicate(client: TestClient, db: Session, owner_token_and_profile, company):
    token, profile = owner_token_and_profile
    data = {"name": company.name, "type": "wholesaler"}
    response = client.post("/companies/create", json=data, headers=auth_headers(token, profile.id))
    assert response.status_code == 400
    assert "이미 존재하는 회사명" in response.json()["detail"]

def test_get_company(client: TestClient, db: Session, company):
    response = client.get(f"/companies/{company.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(company.id)

def test_update_company(client: TestClient, db: Session, owner_token_and_profile, company):
    token, profile = owner_token_and_profile
    update = {"name": "수정회사명", "type": "wholesaler"}
    response = client.put(f"/companies/{company.id}", json=update, headers=auth_headers(token, profile.id))
    assert response.status_code == 200
    assert response.json()["name"] == "수정회사명"

def test_update_company_no_permission(client: TestClient, db: Session, company):
    # 다른 사용자가 수정 시도
    other_user = UserFactory.create_user(db)
    other_profile = ProfileFactory.create_profile(
        db, 
        user_id=other_user.id, 
        type=ProfileType.wholesaler, 
        role=ProfileRole.owner,
        username=f"other_{uuid.uuid4().hex[:8]}"
    )
    token = create_access_token({"sub": str(other_user.id)})
    update = {"name": "권한없음", "type": "wholesaler"}
    response = client.put(f"/companies/{company.id}", json=update, headers=auth_headers(token, other_profile.id))
    assert response.status_code == 403

def test_update_company_owner(client: TestClient, db: Session, owner_token_and_profile, company):
    token, profile = owner_token_and_profile
    new_user = UserFactory.create_user(db)
    new_profile = ProfileFactory.create_profile(
        db, 
        user_id=new_user.id, 
        type=ProfileType.wholesaler, 
        role=ProfileRole.owner,
        username=f"new_owner_{uuid.uuid4().hex[:8]}"
    )
    data = {"new_owner_id": str(new_profile.id)}  # new_user.id가 아닌 new_profile.id로 수정
    response = client.put(f"/companies/{company.id}/owner", json=data, headers=auth_headers(token, profile.id))
    assert response.status_code == 200
    assert response.json()["id"] == str(company.id)

def test_add_company_user(client: TestClient, db: Session, owner_token_and_profile, company):
    token, profile = owner_token_and_profile
    member = ProfileFactory.create_profile(
        db, 
        type=ProfileType.wholesaler, 
        role=ProfileRole.member,
        username=f"member_{uuid.uuid4().hex[:8]}"
    )
    data = {"profile_id": str(member.id), "role": "member"}
    response = client.post(f"/companies/{company.id}/users", json=data, headers=auth_headers(token, profile.id))
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    assert response.status_code == 200
    assert response.json()["id"] == str(member.id)

def test_remove_company_user(client: TestClient, db: Session, owner_token_and_profile, company):
    token, profile = owner_token_and_profile
    member = ProfileFactory.create_profile(
        db, 
        type=ProfileType.wholesaler, 
        role=ProfileRole.member, 
        company_id=company.id,
        username=f"remove_member_{uuid.uuid4().hex[:8]}"
    )
    db.commit()
    response = client.delete(f"/companies/{company.id}/users/{member.id}", headers=auth_headers(token, profile.id))
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    assert response.status_code == 200
    assert response.json()["id"] == str(member.id)

def test_get_my_company(client, db, owner_token_and_profile, company):
    """내 회사 조회 API 테스트"""
    token, profile = owner_token_and_profile
    client.app.dependency_overrides[get_current_profile] = lambda: profile
    profile.company_id = company.id
    db.commit()
    response = client.get(
        "/companies/me",
        headers={"X-Profile-ID": str(profile.id)}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(profile.company_id)
    assert "name" in data
    assert "type" in data 