import pytest
from fastapi.testclient import TestClient
from tests.factories import create_user, create_token_pair


def test_get_my_info(client: TestClient, db):
    user = create_user(db)
    access_token, _ = create_token_pair(user)
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.get("/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(user.id)
    assert data["email"] == user.email
    assert data["name"] == user.name


def test_update_my_info(client: TestClient, db):
    user = create_user(db)
    access_token, _ = create_token_pair(user)
    headers = {"Authorization": f"Bearer {access_token}"}

    update_data = {
        "name": "Updated Name",
    }

    response = client.put(
        "/users/me",
        headers=headers,
        json=update_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]