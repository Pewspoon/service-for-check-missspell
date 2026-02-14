from typing import List
from fastapi import APIRouter, status, Depends
from sqlmodel import Session, select
from database.create_tables import get_session
from models.user import (
    MLPredictionHistory,
    MLPredictionHistoryRead,
)


history_router = APIRouter()


@history_router.post(
    "/ml/history",
    response_model=MLPredictionHistoryRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_history_record(
    user_id: int,
    model_id: int,
    input_text: str,
    result: str,
    cost: float,
    session: Session = Depends(get_session),
) -> MLPredictionHistoryRead:
    """Create a new ML prediction history record."""
    history_record = MLPredictionHistory(
        user_id=user_id,
        model_id=model_id,
        input_text=input_text,
        result=result,
        cost=cost,
    )
    session.add(history_record)
    session.commit()
    session.refresh(history_record)


    return MLPredictionHistoryRead(
        id=history_record.id,
        user_id=history_record.user_id,
        model_id=history_record.model_id,
        input_text=history_record.input_text,
        result=history_record.result,
        cost=history_record.cost,
        created_at=history_record.created_at,
    )


@history_router.get(
    "/ml/history/{user_id}",
    response_model=List[MLPredictionHistoryRead],
    status_code=status.HTTP_200_OK,
)
async def get_user_history(
    user_id: int,
    session: Session = Depends(get_session),
) -> List[MLPredictionHistoryRead]:
    """Get ML prediction history for a user."""
    history_records = session.exec(
        select(MLPredictionHistory).where(
            MLPredictionHistory.user_id == user_id
        )
    ).all()

    result = []
    for record in history_records:
        result.append(
            MLPredictionHistoryRead(
                id=record.id,
                user_id=record.user_id,
                model_id=record.model_id,
                input_text=record.input_text,
                result=record.result,
                cost=record.cost,
                created_at=record.created_at,
            )
        )
    return result
