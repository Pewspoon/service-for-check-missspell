import asyncio

import pytest


pytest.importorskip("fastapi")
pytest.importorskip("bcrypt")
pytest.importorskip("jose")


from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlmodel import select

from models.user import Balance, BalanceReplenishRequest, Transaction
from routes.balance import get_my_balance, replenishment_of_user_balance


def test_get_my_balance_returns_current_amount(session, user_factory):
    user = user_factory(balance_amount=55.0)

    response = asyncio.run(
        get_my_balance(session=session, current_user=user)
    )
    assert response.user_id == user.id
    assert response.amount == 55.0


def test_get_my_balance_returns_404_when_balance_missing(session, user_factory):
    user = user_factory(balance_amount=None)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(get_my_balance(session=session, current_user=user))

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_replenish_creates_balance_when_missing(session, user_factory):
    user = user_factory(balance_amount=None)
    payload = BalanceReplenishRequest(amount=25.0)

    response = asyncio.run(
        replenishment_of_user_balance(
            payload=payload,
            session=session,
            current_user=user,
        )
    )
    assert response.amount == 25.0

    balance = session.exec(select(Balance).where(Balance.user_id == user.id)).first()
    assert balance is not None
    assert balance.amount == 25.0

    txs = session.exec(
        select(Transaction).where(Transaction.user_id == user.id)
    ).all()
    assert len(txs) == 1
    assert txs[0].type == "deposit"
    assert txs[0].amount == 25.0


def test_replenish_increments_existing_balance(session, user_factory):
    user = user_factory(balance_amount=100.0)
    payload = BalanceReplenishRequest(amount=30.0)

    response = asyncio.run(
        replenishment_of_user_balance(
            payload=payload,
            session=session,
            current_user=user,
        )
    )
    assert response.amount == 130.0

    balance = session.exec(select(Balance).where(Balance.user_id == user.id)).first()
    assert balance.amount == 130.0

    txs = session.exec(
        select(Transaction).where(Transaction.user_id == user.id)
    ).all()
    assert len(txs) == 1
    assert txs[0].type == "deposit"
    assert txs[0].amount == 30.0


def test_balance_replenish_request_validation_rejects_non_positive_amount():
    with pytest.raises(ValidationError):
        BalanceReplenishRequest(amount=0)

