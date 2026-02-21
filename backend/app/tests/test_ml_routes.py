import asyncio

import pytest


pytest.importorskip("fastapi")
pytest.importorskip("bcrypt")
pytest.importorskip("jose")
pytest.importorskip("pika")


from fastapi import HTTPException, status
from sqlmodel import select

from models.user import (
    Balance,
    MLPredictionHistory,
    MLPredictionRequest,
    TaskResultRequest,
    Transaction,
)

import routes.ml as ml_routes


def test_ml_predict_success_deducts_balance_and_creates_history(
    session, user_factory, ml_model_factory, monkeypatch
):
    user = user_factory(username="u1", email="u1@example.com", balance_amount=50.0)
    model = ml_model_factory(user_id=user.id, name="m1")

    monkeypatch.setattr(ml_routes, "send_task_to_queue", lambda **_: True)

    response = asyncio.run(
        ml_routes.ml_predict(
            request=MLPredictionRequest(text="hello", model_id=model.id),
            session=session,
            current_user=user,
        )
    )
    assert response.model_name == "m1"

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
    assert history[0].task_id in response.result


def test_ml_predict_forbids_prediction_for_other_user_id(
    session, user_factory, ml_model_factory
):
    user = user_factory(username="u1", email="u1@example.com", balance_amount=50.0)
    model = ml_model_factory(user_id=user.id, name="m1")

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            ml_routes.ml_predict(
                request=MLPredictionRequest(
                    text="hello",
                    model_id=model.id,
                    user_id=user.id + 1,
                ),
                session=session,
                current_user=user,
            )
        )

    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def test_ml_predict_rejects_when_insufficient_balance(
    session, user_factory, ml_model_factory
):
    user = user_factory(username="u1", email="u1@example.com", balance_amount=5.0)
    model = ml_model_factory(user_id=user.id, name="m1")

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            ml_routes.ml_predict(
                request=MLPredictionRequest(text="hello", model_id=model.id),
                session=session,
                current_user=user,
            )
        )

    assert exc.value.status_code == status.HTTP_402_PAYMENT_REQUIRED

    balance = session.exec(select(Balance).where(Balance.user_id == user.id)).first()
    assert balance.amount == 5.0

    txs = session.exec(
        select(Transaction).where(Transaction.user_id == user.id)
    ).all()
    assert txs == []

    history = session.exec(select(MLPredictionHistory)).all()
    assert history == []


def test_ml_predict_refunds_balance_when_queue_send_fails(
    session, user_factory, ml_model_factory, monkeypatch
):
    user = user_factory(username="u1", email="u1@example.com", balance_amount=20.0)
    model = ml_model_factory(user_id=user.id, name="m1")

    monkeypatch.setattr(ml_routes, "send_task_to_queue", lambda **_: False)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            ml_routes.ml_predict(
                request=MLPredictionRequest(text="hello", model_id=model.id),
                session=session,
                current_user=user,
            )
        )
    assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

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
    session, user_factory, ml_model_factory
):
    user = user_factory(username="u1", email="u1@example.com", balance_amount=100.0)
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

    result = asyncio.run(
        ml_routes.receive_task_result(
            request=TaskResultRequest(
                task_id="task-1",
                prediction="OK",
                worker_id="worker-1",
                status="completed",
            ),
            session=session,
        )
    )
    assert result["status"] == "success"

    saved = session.exec(
        select(MLPredictionHistory).where(MLPredictionHistory.task_id == "task-1")
    ).first()
    assert saved.result == "OK"


def test_receive_task_result_returns_error_when_task_not_found(session):
    result = asyncio.run(
        ml_routes.receive_task_result(
            request=TaskResultRequest(
                task_id="missing",
                prediction="OK",
                worker_id="worker-1",
                status="completed",
            ),
            session=session,
        )
    )
    assert result["status"] == "error"
    assert result["message"] == "Task not found"


def test_get_prediction_result_pending_and_completed(
    session, user_factory, ml_model_factory
):
    user = user_factory(username="u1", email="u1@example.com", balance_amount=100.0)
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

    pending = asyncio.run(
        ml_routes.get_prediction_result(
            task_id="task-1",
            session=session,
            current_user=user,
        )
    )
    assert pending["status"] == "pending"

    record.result = "OK"
    session.add(record)
    session.commit()

    completed = asyncio.run(
        ml_routes.get_prediction_result(
            task_id="task-1",
            session=session,
            current_user=user,
        )
    )
    assert completed["status"] == "completed"
    assert completed["result"] == "OK"


def test_get_prediction_result_returns_404_for_other_user(
    session, user_factory, ml_model_factory
):
    owner = user_factory(username="u1", email="u1@example.com", balance_amount=100.0)
    other = user_factory(username="u2", email="u2@example.com", balance_amount=100.0)
    model = ml_model_factory(user_id=owner.id, name="m1")

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

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            ml_routes.get_prediction_result(
                task_id="task-1",
                session=session,
                current_user=other,
            )
        )
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND

