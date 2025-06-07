import pytest
from fastapi.testclient import TestClient
from app.user.models import User
from app.core.auth.utils import create_access_token

@pytest.fixture
def auth_headers(test_user: User):
    access_token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}



def test_get_my_info(client: TestClient, test_user: User, auth_headers: dict):
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["email"] == test_user.email
    assert data["name"] == test_user.name

def test_update_my_info(client: TestClient, test_user: User, auth_headers: dict):
    update_data = {
        "name": "Updated Name",
    }
    
    response = client.put(
        "/users/me",
        headers=auth_headers,
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]

