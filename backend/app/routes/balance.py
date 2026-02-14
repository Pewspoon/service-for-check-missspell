from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from database.create_tables import get_session
from models.user import Balance, Transaction

balance_of_user_route = APIRouter()


@balance_of_user_route.get(
    "/ml/balance/{user_id}",
    status_code=status.HTTP_200_OK,
)
async def get_ml_balance(
    user_id: int,
    session: Session = Depends(get_session),
) -> dict:
    """Get user balance."""
    balance = session.exec(
        select(Balance).where(Balance.user_id == user_id)
    ).first()
    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Balance not found",
        )
    return {"user_id": user_id, "amount": balance.amount}


@balance_of_user_route.post(
    "/balance/replenish/{user_id}",
    status_code=status.HTTP_200_OK,
)
async def replenishment_of_user_balance(
    user_id: int,
    amount: float,
    session: Session = Depends(get_session),
) -> dict:
    """Replenish user balance."""
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than 0",
        )

    balance = session.exec(
        select(Balance).where(Balance.user_id == user_id)
    ).first()

    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Balance not found",
        )

    # Update balance of user
    balance.amount += amount
    session.add(balance)

    # Create transaction record of update balance
    transaction = Transaction(
        user_id=user_id,
        amount=amount,
        type="deposit",
        description="Balance replenishment"
    )
    session.add(transaction)

    session.commit()
    session.refresh(balance)

    return {"user_id": user_id, "amount": balance.amount}