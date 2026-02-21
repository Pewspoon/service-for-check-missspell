import asyncio

import pytest


pytest.importorskip("fastapi")
pytest.importorskip("bcrypt")
pytest.importorskip("jose")


from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlmodel import select

from models.user import Balance, User, UserCreate
from routes.user import get_me, login_user, register_user


class DummyFormData:
    def __init__(self, *, username: str, password: str):
        self.username = username
        self.password = password


def test_register_user_creates_user_and_initial_balance(session):
    payload = UserCreate(
        username="alice",
        email="alice@example.com",
        full_name="Alice",
        password="secret",
    )

    response = asyncio.run(register_user(payload=payload, session=session))
    assert response.id > 0
    assert response.username == "alice"
    assert response.email == "alice@example.com"

    user = session.exec(select(User).where(User.id == response.id)).first()
    assert user is not None
    assert user.hashed_password != "secret"

    balance = session.exec(select(Balance).where(Balance.user_id == user.id)).first()
    assert balance is not None
    assert balance.amount == 100


def test_register_user_duplicate_username_or_email_returns_409(session):
    payload = UserCreate(
        username="alice",
        email="alice@example.com",
        full_name="Alice",
        password="secret",
    )
    asyncio.run(register_user(payload=payload, session=session))

    with pytest.raises(HTTPException) as exc:
        asyncio.run(register_user(payload=payload, session=session))

    assert exc.value.status_code == status.HTTP_409_CONFLICT


def test_login_user_success_returns_jwt_token(session):
    payload = UserCreate(
        username="bob",
        email="bob@example.com",
        full_name="Bob",
        password="secret",
    )
    asyncio.run(register_user(payload=payload, session=session))

    token = asyncio.run(
        login_user(
            form_data=DummyFormData(username="bob", password="secret"),
            session=session,
        )
    )
    assert token.token_type == "bearer"
    assert isinstance(token.access_token, str)
    assert token.access_token


def test_login_user_invalid_credentials_returns_401(session):
    payload = UserCreate(
        username="bob",
        email="bob@example.com",
        full_name="Bob",
        password="secret",
    )
    asyncio.run(register_user(payload=payload, session=session))

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            login_user(
                form_data=DummyFormData(username="bob", password="wrong"),
                session=session,
            )
        )

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_user_can_be_called_twice(session):
    payload = UserCreate(
        username="bob",
        email="bob@example.com",
        full_name="Bob",
        password="secret",
    )
    asyncio.run(register_user(payload=payload, session=session))

    token1 = asyncio.run(
        login_user(
            form_data=DummyFormData(username="bob", password="secret"),
            session=session,
        )
    )
    token2 = asyncio.run(
        login_user(
            form_data=DummyFormData(username="bob", password="secret"),
            session=session,
        )
    )
    assert token1.access_token
    assert token2.access_token


def test_get_me_returns_current_user_response(user_factory):
    user = user_factory(username="carol", email="carol@example.com")
    response = asyncio.run(get_me(current_user=user))

    assert response.id == user.id
    assert response.username == user.username
    assert response.email == user.email


def test_user_create_validation_rejects_short_username():
    with pytest.raises(ValidationError):
        UserCreate(
            username="ab",
            email="a@example.com",
            password="secret",
        )
