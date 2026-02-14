from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from database.create_tables import get_session
from models.user import (
    Balance,
    MLModel,
    MLPredictionRequest,
    MLPredictionResponse,
)


ml_router = APIRouter()

PREDICTION_COST = 10.0


@ml_router.get(
    "/ml/balance/{user_id}",
    status_code=status.HTTP_200_OK,
)
async def get_ml_balance(
    user_id: int,
    session: Session = Depends(get_session),
) -> dict:
    balance = session.exec(
        select(Balance).where(Balance.user_id == user_id)
    ).first()
    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Balance not found",
        )
    return {"user_id": user_id, "amount": balance.amount}


@ml_router.post(
    "/ml/predict",
    response_model=MLPredictionResponse,
    status_code=status.HTTP_200_OK,
)
async def ml_predict(
    request: MLPredictionRequest,
    session: Session = Depends(get_session),
) -> MLPredictionResponse:
    """Get prediction from ML model with balance check."""
    ml_model = session.exec(
        select(MLModel).where(MLModel.id == request.model_id)
    ).first()
    if not ml_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {request.model_id} not found",
        )

    balance = session.exec(
        select(Balance).where(Balance.user_id == request.user_id)
    ).first()
    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User balance is negative",
        )
    if balance.amount < PREDICTION_COST:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"Insufficient balance. Required: {PREDICTION_COST}, "
                f"Available: {balance.amount}"
            ),
        )

    balance.amount -= PREDICTION_COST
    session.add(balance)
    session.commit()

    return MLPredictionResponse(
        result="prediction_result",
        model_name=ml_model.name,
    )
