import asyncio

import pytest


pytest.importorskip("fastapi")
pytest.importorskip("bcrypt")
pytest.importorskip("jose")


from sqlmodel import select

from models.user import MLPredictionHistory
from routes.history_of_ml_transaction import create_history_record, get_my_history


def test_create_history_record_saves_ml_history(session, user_factory, ml_model_factory):
    user = user_factory(username="u1", email="u1@example.com")
    model = ml_model_factory(user_id=user.id, name="m1")

    response = asyncio.run(
        create_history_record(
            model_id=model.id,
            input_text="hello",
            result="OK",
            cost=10.0,
            session=session,
            current_user=user,
        )
    )
    assert response.user_id == user.id
    assert response.model_id == model.id
    assert response.input_text == "hello"
    assert response.result == "OK"
    assert response.cost == 10.0

    saved = session.exec(
        select(MLPredictionHistory).where(MLPredictionHistory.id == response.id)
    ).first()
    assert saved is not None
    assert saved.user_id == user.id


def test_get_my_history_returns_only_current_users_history(
    session, user_factory, ml_model_factory
):
    user1 = user_factory(username="u1", email="u1@example.com")
    user2 = user_factory(username="u2", email="u2@example.com")
    model1 = ml_model_factory(user_id=user1.id, name="m1")
    model2 = ml_model_factory(user_id=user2.id, name="m2")

    asyncio.run(
        create_history_record(
            model_id=model1.id,
            input_text="t1",
            result="r1",
            cost=1.0,
            session=session,
            current_user=user1,
        )
    )
    asyncio.run(
        create_history_record(
            model_id=model2.id,
            input_text="t2",
            result="r2",
            cost=2.0,
            session=session,
            current_user=user2,
        )
    )

    history1 = asyncio.run(get_my_history(session=session, current_user=user1))
    assert len(history1) == 1
    assert history1[0].user_id == user1.id
    assert history1[0].input_text == "t1"

    history2 = asyncio.run(get_my_history(session=session, current_user=user2))
    assert len(history2) == 1
    assert history2[0].user_id == user2.id
    assert history2[0].input_text == "t2"


def test_get_my_history_returns_empty_list_when_no_records(session, user_factory):
    user = user_factory(username="u1", email="u1@example.com")
    history = asyncio.run(get_my_history(session=session, current_user=user))
    assert history == []

