from typing import Any
import pytest
from fastapi.testclient import TestClient
from app import schemas
from jose import jwt
from app.core import settings


def test_create_user(client: TestClient) -> None:
    res = client.post(
        "/users", json={"email": "second@example.com", "password": "password123"}
    )
    new_user = schemas.UserResponse(**res.json())
    assert new_user.email == "second@example.com"
    assert res.status_code == 201


def test_login_user(test_user: dict[str, Any], client: TestClient) -> None:
    res = client.post(
        "/auth",
        data={
            "username": test_user["email"],
            "password": test_user["password"],
        },
    )
    assert res.status_code == 200
    token = schemas.Token(**res.json())
    payload = jwt.decode(
        token.access_token, settings.secret_key, algorithms=[settings.algorithm]
    )
    username = payload.get("sub")
    assert username == test_user["email"]
    assert token.token_type == "bearer"


@pytest.mark.parametrize(
    "email, password, status_code",
    [
        ("wrong1@gmail.com", "password123", 401),
        ("wrong2@gmail.com", "password123", 401),
        ("test@example.com", "wrongpassword1", 401),
        ("test@example.com", "wrongpassword2", 401),
        ("wrong3@gmail.com", "wrongpassword3", 401),
        ("test@example.com", None, 401),
        (None, "password123", 401),
    ],
)
def test_incorrect_login(
    test_user: dict[str, Any],
    client: TestClient,
    email: str,
    password: str,
    status_code: str,
) -> None:
    res = client.post("/auth", data={"username": email, "password": password})
    assert res.status_code == status_code
    assert res.json().get("detail") == "Invalid Credentials"
