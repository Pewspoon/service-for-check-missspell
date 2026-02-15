from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from database.create_tables import get_session
from models.user import (
    Balance,
    MLModel,
    MLPredictionRequest,
    MLPredictionResponse,
    MLPredictionHistory,
    Transaction,
    User,
)
from auth import get_current_active_user
import logging

logger = logging.getLogger(__name__)

ml_router = APIRouter()

PREDICTION_COST = 10.0


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
        # Здесь должен быть вызов ML модели
        # Например: result = await call_ml_model(ml_model, request.text)
        result = "prediction_result"  # Заглушка для демонстрации

        # Создаём запись в истории предсказаний
        history_record = MLPredictionHistory(
            user_id=current_user.id,
            model_id=ml_model.id,
            input_text=request.text,
            result=result,
            cost=PREDICTION_COST,
        )
        session.add(history_record)
        session.commit()

        return MLPredictionResponse(
            result=result,
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
