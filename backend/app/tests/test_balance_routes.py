import pytest


pytest.importorskip("fastapi")
pytest.importorskip("bcrypt")
pytest.importorskip("jose")


from sqlmodel import select

from models.user import Balance, Transaction


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


def test_get_my_balance_returns_current_amount(client):
    _register(
        client,
        username="balance_user",
        email="balance_user@example.com",
        password="secret",
    )
    login = _login(client, username="balance_user", password="secret")
    token = login.json()["access_token"]

    response = client.get(
        "/api/balance/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["amount"] == 100


def test_get_my_balance_returns_404_when_balance_missing(client, user_factory):
    user = user_factory(balance_amount=None)
    login = _login(client, username=user.username, password="password")
    token = login.json()["access_token"]

    response = client.get(
        "/api/balance/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_replenish_creates_balance_when_missing(client, session, user_factory):
    user = user_factory(balance_amount=None)
    login = _login(client, username=user.username, password="password")
    token = login.json()["access_token"]

    response = client.post(
        "/api/balance/replenish",
        headers={"Authorization": f"Bearer {token}"},
        json={"amount": 25.0},
    )
    assert response.status_code == 200
    assert response.json()["amount"] == 25.0

    balance = session.exec(select(Balance).where(Balance.user_id == user.id)).first()
    assert balance is not None
    assert balance.amount == 25.0

    txs = session.exec(
        select(Transaction).where(Transaction.user_id == user.id)
    ).all()
    assert len(txs) == 1
    assert txs[0].type == "deposit"
    assert txs[0].amount == 25.0


def test_replenish_increments_existing_balance(client, session):
    register = _register(
        client,
        username="inc_user",
        email="inc_user@example.com",
        password="secret",
    )
    user_id = register.json()["id"]
    login = _login(client, username="inc_user", password="secret")
    token = login.json()["access_token"]

    response = client.post(
        "/api/balance/replenish",
        headers={"Authorization": f"Bearer {token}"},
        json={"amount": 30.0},
    )
    assert response.status_code == 200
    assert response.json()["amount"] == 130.0

    balance = session.exec(select(Balance).where(Balance.user_id == user_id)).first()
    assert balance.amount == 130.0

    txs = session.exec(
        select(Transaction).where(Transaction.user_id == user_id)
    ).all()
    assert len(txs) == 1
    assert txs[0].type == "deposit"
    assert txs[0].amount == 30.0


def test_balance_replenish_request_validation_rejects_non_positive_amount(client):
    _register(
        client,
        username="valid_user",
        email="valid_user@example.com",
        password="secret",
    )
    login = _login(client, username="valid_user", password="secret")
    token = login.json()["access_token"]

    response = client.post(
        "/api/balance/replenish",
        headers={"Authorization": f"Bearer {token}"},
        json={"amount": 0},
    )
    assert response.status_code == 422
