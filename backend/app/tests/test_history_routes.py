import pytest
pytest.importorskip("fastapi")
pytest.importorskip("bcrypt")
pytest.importorskip("jose")
from sqlmodel import select

from models.user import MLPredictionHistory


def _login(client, *, username: str, password: str):
    return client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )


def test_create_history_record_saves_ml_history(client, session, user_factory, ml_model_factory):
    user = user_factory(username="user1", email="user1@example.com")
    model = ml_model_factory(user_id=user.id, name="m1")
    login = _login(client, username=user.username, password="password")
    token = login.json()["access_token"]

    response = client.post(
        "/api/history/ml/history",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "model_id": model.id,
            "input_text": "hello",
            "result": "OK",
            "cost": 10.0,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["user_id"] == user.id
    assert body["model_id"] == model.id
    assert body["input_text"] == "hello"
    assert body["result"] == "OK"
    assert body["cost"] == 10.0

    saved = session.exec(
        select(MLPredictionHistory).where(MLPredictionHistory.id == body["id"])
    ).first()
    assert saved is not None
    assert saved.user_id == user.id


def test_get_my_history_returns_only_current_users_history(
    client, session, user_factory, ml_model_factory
):
    user1 = user_factory(username="user1", email="user1@example.com")
    user2 = user_factory(username="user2", email="user2@example.com")
    model1 = ml_model_factory(user_id=user1.id, name="m1")
    model2 = ml_model_factory(user_id=user2.id, name="m2")
    token1 = _login(client, username=user1.username, password="password").json()["access_token"]
    token2 = _login(client, username=user2.username, password="password").json()["access_token"]

    create_1 = client.post(
        "/api/history/ml/history",
        headers={"Authorization": f"Bearer {token1}"},
        params={
            "model_id": model1.id,
            "input_text": "t1",
            "result": "r1",
            "cost": 1.0,
        },
    )
    create_2 = client.post(
        "/api/history/ml/history",
        headers={"Authorization": f"Bearer {token2}"},
        params={
            "model_id": model2.id,
            "input_text": "t2",
            "result": "r2",
            "cost": 2.0,
        },
    )
    assert create_1.status_code == 201
    assert create_2.status_code == 201

    history1 = client.get(
        "/api/history/me",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert history1.status_code == 200
    history1_body = history1.json()
    assert len(history1_body) == 1
    assert history1_body[0]["user_id"] == user1.id
    assert history1_body[0]["input_text"] == "t1"

    history2 = client.get(
        "/api/history/me",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert history2.status_code == 200
    history2_body = history2.json()
    assert len(history2_body) == 1
    assert history2_body[0]["user_id"] == user2.id
    assert history2_body[0]["input_text"] == "t2"


def test_get_my_history_returns_empty_list_when_no_records(client, user_factory):
    user = user_factory(username="user1", email="user1@example.com")
    token = _login(client, username=user.username, password="password").json()["access_token"]
    history = client.get(
        "/api/history/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert history.status_code == 200
    assert history.json() == []
