import pytest
from sqlmodel import select
from models.user import (
    Balance,
    MLPredictionHistory,
    Transaction,
)
import routes.ml as ml_routes
pytest.importorskip("fastapi")
pytest.importorskip("bcrypt")
pytest.importorskip("jose")
pytest.importorskip("pika")


def _login(client, *, username: str, password: str):
    response = client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_ml_predict_success_deducts_balance_and_creates_history(
    client, session, user_factory, ml_model_factory, monkeypatch
):
    user = user_factory(username="user1", email="user1@example.com", balance_amount=50.0)
    model = ml_model_factory(user_id=user.id, name="m1")
    headers = _login(client, username=user.username, password="password")

    monkeypatch.setattr(ml_routes, "send_task_to_queue", lambda **_: True)

    response = client.post(
        "/api/predict/predict",
        headers=headers,
        json={"text": "hello", "model_id": model.id},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["model_name"] == "m1"

    balance = session.exec(select(Balance).where(Balance.user_id == user.id)).first()
    assert balance.amount == 50.0 - ml_routes.PREDICTION_COST

    txs = session.exec(
        select(Transaction).where(Transaction.user_id == user.id)
    ).all()
    assert len(txs) == 1
    assert txs[0].type == "withdrawal"
    assert txs[0].amount == ml_routes.PREDICTION_COST

    history = session.exec(
        select(MLPredictionHistory).where(MLPredictionHistory.user_id == user.id)
    ).all()
    assert len(history) == 1
    assert history[0].task_id is not None
    assert history[0].result.startswith("PENDING:")
    assert history[0].task_id in body["result"]


def test_ml_predict_forbids_prediction_for_other_user_id(
    client, user_factory, ml_model_factory
):
    user = user_factory(username="user1", email="user1@example.com", balance_amount=50.0)
    model = ml_model_factory(user_id=user.id, name="m1")
    headers = _login(client, username=user.username, password="password")

    response = client.post(
        "/api/predict/predict",
        headers=headers,
        json={"text": "hello", "model_id": model.id, "user_id": user.id + 1},
    )
    assert response.status_code == 403


def test_ml_predict_rejects_when_insufficient_balance(
    client, session, user_factory, ml_model_factory
):
    user = user_factory(username="user1", email="user1@example.com", balance_amount=5.0)
    model = ml_model_factory(user_id=user.id, name="m1")
    headers = _login(client, username=user.username, password="password")

    response = client.post(
        "/api/predict/predict",
        headers=headers,
        json={"text": "hello", "model_id": model.id},
    )
    assert response.status_code == 402

    balance = session.exec(select(Balance).where(Balance.user_id == user.id)).first()
    assert balance.amount == 5.0

    txs = session.exec(
        select(Transaction).where(Transaction.user_id == user.id)
    ).all()
    assert txs == []

    history = session.exec(select(MLPredictionHistory)).all()
    assert history == []


def test_ml_predict_refunds_balance_when_queue_send_fails(
    client, session, user_factory, ml_model_factory, monkeypatch
):
    user = user_factory(username="user1", email="user1@example.com", balance_amount=20.0)
    model = ml_model_factory(user_id=user.id, name="m1")
    headers = _login(client, username=user.username, password="password")

    monkeypatch.setattr(ml_routes, "send_task_to_queue", lambda **_: False)

    response = client.post(
        "/api/predict/predict",
        headers=headers,
        json={"text": "hello", "model_id": model.id},
    )
    assert response.status_code == 500

    balance = session.exec(select(Balance).where(Balance.user_id == user.id)).first()
    assert balance.amount == 20.0

    txs = session.exec(
        select(Transaction).where(Transaction.user_id == user.id)
    ).all()
    assert len(txs) == 2
    assert {tx.type for tx in txs} == {"withdrawal", "deposit"}

    history = session.exec(select(MLPredictionHistory)).all()
    assert history == []


def test_receive_task_result_updates_history_record(
    client, session, user_factory, ml_model_factory
):
    user = user_factory(username="user1", email="user1@example.com", balance_amount=100.0)
    model = ml_model_factory(user_id=user.id, name="m1")

    record = MLPredictionHistory(
        user_id=user.id,
        model_id=model.id,
        input_text="hello",
        result="PENDING:task-1",
        cost=ml_routes.PREDICTION_COST,
        task_id="task-1",
    )
    session.add(record)
    session.commit()

    result = client.post(
        "/api/predict/send_task_result",
        json={
            "task_id": "task-1",
            "prediction": "OK",
            "worker_id": "worker-1",
            "status": "completed",
        },
    )
    assert result.status_code == 200
    assert result.json()["status"] == "success"

    saved = session.exec(
        select(MLPredictionHistory).where(MLPredictionHistory.task_id == "task-1")
    ).first()
    assert saved.result == "OK"


def test_receive_task_result_returns_error_when_task_not_found(client):
    result = client.post(
        "/api/predict/send_task_result",
        json={
            "task_id": "missing",
            "prediction": "OK",
            "worker_id": "worker-1",
            "status": "completed",
        },
    )
    assert result.status_code == 200
    assert result.json()["status"] == "error"
    assert result.json()["message"] == "Task not found"


def test_get_prediction_result_pending_and_completed(
    client, session, user_factory, ml_model_factory
):
    user = user_factory(username="user1", email="user1@example.com", balance_amount=100.0)
    model = ml_model_factory(user_id=user.id, name="m1")
    headers = _login(client, username=user.username, password="password")

    record = MLPredictionHistory(
        user_id=user.id,
        model_id=model.id,
        input_text="hello",
        result="PENDING:task-1",
        cost=ml_routes.PREDICTION_COST,
        task_id="task-1",
    )
    session.add(record)
    session.commit()

    pending = client.get(
        "/api/predict/result/task-1",
        headers=headers,
    )
    assert pending.status_code == 200
    assert pending.json()["status"] == "pending"

    record.result = "OK"
    session.add(record)
    session.commit()

    completed = client.get(
        "/api/predict/result/task-1",
        headers=headers,
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert completed.json()["result"] == "OK"


def test_get_prediction_result_returns_404_for_other_user(
    client, session, user_factory, ml_model_factory
):
    owner = user_factory(username="user1", email="user1@example.com", balance_amount=100.0)
    other = user_factory(username="user2", email="user2@example.com", balance_amount=100.0)
    model = ml_model_factory(user_id=owner.id, name="m1")
    other_headers = _login(client, username=other.username, password="password")

    session.add(
        MLPredictionHistory(
            user_id=owner.id,
            model_id=model.id,
            input_text="hello",
            result="OK",
            cost=ml_routes.PREDICTION_COST,
            task_id="task-1",
        )
    )
    session.commit()

    response = client.get(
        "/api/predict/result/task-1",
        headers=other_headers,
    )
    assert response.status_code == 404
