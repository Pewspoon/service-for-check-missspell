from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from database.create_tables import get_session
from models.user import UserCreate, User

user_route = APIRouter()


@user_route.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=User,
)
async def register_user(
    payload: UserCreate,
    session: Session = Depends(get_session),
) -> User:
    # Проверка уникальности email и username
    existing_user = session.exec(
        select(User).where(
            (User.email == payload.email) | (User.username == payload.username)
        )
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email or username already exists",
        )

    user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role,
        hashed_password=payload.password,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@user_route.post(
    "/autorisation",
    status_code=status.HTTP_200_OK,
)
async def autorisation_user(
    payload: UserCreate,
    session: Session = Depends(get_session),
) -> dict:
    user = session.exec(
        select(User).where(User.email == payload.email)
    ).first()
    if not user or user.hashed_password != payload.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return {"username": user.username, "message": "Welcome!"}
