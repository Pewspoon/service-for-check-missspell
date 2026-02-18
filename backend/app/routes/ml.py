from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from models.user import TaskResultRequest
from database.create_tables import get_session
from auth import get_current_active_user
#from ml_worker.rmqconf import RabbitMQConfig
from datetime import datetime
from models.user import (
    Balance,
    MLModel,
    MLPredictionRequest,
    MLPredictionResponse,
    MLPredictionHistory,
    Transaction,
    User,
)
from pydantic import BaseModel
import logging
import pika
import json
import uuid

logger = logging.getLogger(__name__)

ml_router = APIRouter()

PREDICTION_COST = 10.0

# Конфигурация RabbitMQ
#rabbitmq_config = RabbitMQConfig()


def send_task_to_queue(
    task_id: str, model_name: str, features: dict
) -> bool:
    """
    Отправляет задачу в RabbitMQ очередь.
    """
    try:
        credentials = pika.PlainCredentials('admin', 'password123')
        parameters = pika.ConnectionParameters(
            host='rabbitmq',
            port=5672,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue='ml_task_queue', durable=True)

        task_data = {
            'task_id': task_id,
            'features': features,
            'model': model_name,
            'timestamp': datetime.utcnow().isoformat()
        }

        channel.basic_publish(
            exchange='',
            routing_key='ml_task_queue',
            body=json.dumps(task_data),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        connection.close()
        logger.info(f"Task {task_id} sent to queue")
        return True
    except Exception as e:
        logger.error(f"Failed to send task to queue: {e}")
        return False


@ml_router.get(
    "/balance",
    status_code=status.HTTP_200_OK,
)
async def get_ml_balance(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Получить баланс текущего пользователя для ML-предсказаний."""
    balance = session.exec(
        select(Balance).where(Balance.user_id == current_user.id)
    ).first()
    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Balance not found",
        )
    return {"user_id": current_user.id, "amount": balance.amount}


@ml_router.post(
    "/predict",
    response_model=MLPredictionResponse,
    status_code=status.HTTP_200_OK,
)
async def ml_predict(
    request: MLPredictionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> MLPredictionResponse:
    """Получить предсказание от ML-модели с проверкой баланса."""
    # Verify user can only access their own predictions
    if request.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only make predictions for yourself",
        )

    ml_model = session.exec(
        select(MLModel).where(MLModel.id == request.model_id)
    ).first()
    if not ml_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {request.model_id} not found",
        )

    balance = session.exec(
        select(Balance).where(Balance.user_id == current_user.id)
    ).first()
    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User balance not found",
        )
    if balance.amount < PREDICTION_COST:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"Insufficient balance. Required: {PREDICTION_COST}, "
                f"Available: {balance.amount}"
            ),
        )

    # Списываем средства
    balance.amount -= PREDICTION_COST
    session.add(balance)

    # Создаём запись о транзакции списания
    transaction = Transaction(
        user_id=current_user.id,
        amount=PREDICTION_COST,
        type="withdrawal",
        description=f"ML prediction with model {ml_model.name}"
    )
    session.add(transaction)

    try:
        # Генерируем уникальный ID задачи
        task_id = str(uuid.uuid4())
        
        # Отправляем задачу в очередь
        if not send_task_to_queue(
            task_id=task_id,
            model_name=ml_model.name,
            features={'text': request.text}
        ):
            raise Exception("Failed to send task to queue")
        
        # Создаём запись в истории предсказаний с task_id и статусом PENDING
        history_record = MLPredictionHistory(
            user_id=current_user.id,
            model_id=ml_model.id,
            input_text=request.text,
            task_id=task_id,                      # <-- добавлено поле task_id
            result=f"PENDING:{task_id}",          # можно оставить так (совместимость) или изменить на "PENDING"
            cost=PREDICTION_COST,
        )
        session.add(history_record)
        session.commit()

        return MLPredictionResponse(
            result=f"Task {task_id} queued for processing",
            model_name=ml_model.name,
        )

    except Exception as e:
        # При ошибке ML возвращаем средства пользователю
        logger.error(f"ML prediction failed: {e}")
        
        # Возвращаем средства
        balance.amount += PREDICTION_COST
        session.add(balance)

        # Создаём запись о транзакции возврата
        refund_transaction = Transaction(
            user_id=current_user.id,
            amount=PREDICTION_COST,
            type="deposit",
            description=f"Refund due to ML prediction error: {str(e)}"
        )
        session.add(refund_transaction)
        session.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"ML prediction failed. Funds returned to balance. "
                f"Error: {str(e)}"
            ),
        )


@ml_router.post("/send_task_result")
async def receive_task_result(
    request: TaskResultRequest,
    session: Session = Depends(get_session),
):
    """
    Получает результат от воркера и обновляет запись в БД.

    Этот эндпоинт вызывается ML-воркером после обработки задачи.

    Args:
        request: JSON с полями task_id, prediction, worker_id, status
        session: Сессия базы данных

    Returns:
        dict: Статус операции
    """
    try:
        history_record = session.exec(
            select(MLPredictionHistory).where(
                MLPredictionHistory.task_id == request.task_id
            )
        ).first()

        if not history_record:
            logger.error(f"Task {request.task_id} not found in history")
            return {"status": "error", "message": "Task not found"}

        # Обновляем результат
        history_record.result = request.prediction
        session.add(history_record)
        session.commit()

        logger.info(
            f"Task {request.task_id} result saved by {request.worker_id}: "
            f"{request.prediction[:50]}..."
        )
        return {"status": "success", "task_id": request.task_id}

    except Exception as e:
        logger.error(f"Error saving task result: {e}")
        return {"status": "error", "message": str(e)}
    

@ml_router.get("/result/{task_id}")
async def get_prediction_result(
    task_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """
    Получить результат предсказания по task_id.
    Доступно только для авторизованного пользователя, которому принадлежит задача.
    """
    # Ищем запись по task_id и user_id (для безопасности)
    record = session.exec(
        select(MLPredictionHistory).where(
            MLPredictionHistory.task_id == task_id,
            MLPredictionHistory.user_id == current_user.id
        )
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or you don't have access"
        )

    # Если задача ещё в обработке
    if record.result.startswith("PENDING"):
        return {
            "status": "pending",
            "task_id": task_id,
            "message": "Task is still being processed"
        }

    # Задача завершена, возвращаем результат
    return {
        "status": "completed",
        "task_id": task_id,
        "result": record.result,
        "model_id": record.model_id,
        "created_at": record.created_at.isoformat() if record.created_at else None
    }