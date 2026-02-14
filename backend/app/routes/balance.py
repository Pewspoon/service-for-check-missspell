from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from database.create_tables import get_session
from models.user import Balance

balance_of_user_route = APIRouter()

@balance_of_user_route.get(
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


@balance_of_user_route.get(
    "/balance/balance/{user_id}",
    status_code=status.HTTP_200_OK,
)
async def replenishment_of_user_balance(
    user_id: int,
    session: Session = Depends(get_session),
    amount_of_replenishment: int
) -> dict:
    balance = session.exec(
        select(Balance).where(Balance.user_id == user_id)
    ).first()
    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Balance is not replenishment!",
        )
    balance = balance + amount_of_replenishment
    return {"user_id": user_id, "amount": balance.amount}