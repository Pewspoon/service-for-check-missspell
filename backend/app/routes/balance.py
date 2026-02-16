from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from database.create_tables import get_session
from models.user import (
    Balance,
    Transaction,
    User,
    BalanceResponse,
    BalanceReplenishRequest,
)
from auth import get_current_active_user

balance_of_user_route = APIRouter()


@balance_of_user_route.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=BalanceResponse,
)
async def get_my_balance(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> BalanceResponse:
    """Получить баланс текущего пользователя."""
    balance = session.exec(
        select(Balance).where(Balance.user_id == current_user.id)
    ).first()
    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Balance not found",
        )
    return BalanceResponse(user_id=current_user.id, amount=balance.amount)


@balance_of_user_route.post(
    "/replenish",
    status_code=status.HTTP_200_OK,
    response_model=BalanceResponse,
)
async def replenishment_of_user_balance(
    payload: BalanceReplenishRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> BalanceResponse:
    """Пополнить баланс текущего пользователя."""
    balance = session.exec(
        select(Balance).where(Balance.user_id == current_user.id)
    ).first()

    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Balance not found",
        )

    # Update balance of user
    balance.amount += payload.amount
    session.add(balance)

    # Create transaction record of update balance
    transaction = Transaction(
        user_id=current_user.id,
        amount=payload.amount,
        type="deposit",
        description="Balance replenishment"
    )
    session.add(transaction)

    session.commit()
    session.refresh(balance)

    return BalanceResponse(user_id=current_user.id, amount=balance.amount)
