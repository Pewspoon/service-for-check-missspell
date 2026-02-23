import pytest


pytest.importorskip("fastapi")
pytest.importorskip("bcrypt")
pytest.importorskip("jose")


from sqlmodel import select

from models.user import Balance, User


def _register(client, *, username: str, email: str, password: str):
    return client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "full_name": username.title(),
            "password": password,
            "role": "user",
        },
    )


def _login(client, *, username: str, password: str):
    return client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )


def test_register_user_creates_user_and_initial_balance(client, session):
    response = _register(
        client,
        username="alice",
        email="alice@example.com",
        password="secret",
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"

    user = session.exec(select(User).where(User.id == body["id"])).first()
    assert user is not None
    assert user.hashed_password != "secret"

    balance = session.exec(select(Balance).where(Balance.user_id == user.id)).first()
    assert balance is not None
    assert balance.amount == 100


def test_register_user_duplicate_username_or_email_returns_409(client):
    first = _register(
        client,
        username="alice",
        email="alice@example.com",
        password="secret",
    )
    assert first.status_code == 201

    second = _register(
        client,
        username="alice",
        email="alice@example.com",
        password="secret",
    )
    assert second.status_code == 409


def test_login_user_success_returns_jwt_token(client):
    _register(
        client,
        username="bob",
        email="bob@example.com",
        password="secret",
    )

    response = _login(client, username="bob", password="secret")
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]


def test_login_user_invalid_credentials_returns_401(client):
    _register(
        client,
        username="bob",
        email="bob@example.com",
        password="secret",
    )

    response = _login(client, username="bob", password="wrong")
    assert response.status_code == 401


def test_login_user_can_be_called_twice(client):
    _register(
        client,
        username="bob",
        email="bob@example.com",
        password="secret",
    )

    token1 = _login(client, username="bob", password="secret")
    token2 = _login(client, username="bob", password="secret")
    assert token1.status_code == 200
    assert token2.status_code == 200
    assert token1.json()["access_token"]
    assert token2.json()["access_token"]


def test_get_me_returns_current_user_response(client):
    register = _register(
        client,
        username="carol",
        email="carol@example.com",
        password="secret",
    )
    user_id = register.json()["id"]

    login = _login(client, username="carol", password="secret")
    token = login.json()["access_token"]
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == user_id
    assert body["username"] == "carol"
    assert body["email"] == "carol@example.com"


def test_user_create_validation_rejects_short_username(client):
    response = _register(
        client,
        username="ab",
        email="a@example.com",
        password="secret",
    )
    assert response.status_code == 422
