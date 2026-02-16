from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import timedelta
from database.create_tables import get_session
from models.user import UserCreate, User, UserResponse, TokenResponse, AuthorizationResponse
from auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user,
)
from database.config import get_settings

user_route = APIRouter()
settings = get_settings()


@user_route.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
)
async def register_user(
    payload: UserCreate,
    session: Session = Depends(get_session),
) -> UserResponse:
    """Зарегистрировать нового пользователя с хешированным паролем."""
    # Check for unique email and username
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
        hashed_password=get_password_hash(payload.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )



@user_route.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=TokenResponse,
)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> TokenResponse:
    """Авторизовать пользователя и вернуть JWT access token."""
    user = session.exec(
        select(User).where(User.username == form_data.username)
    ).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return TokenResponse(access_token=access_token, token_type="bearer")


@user_route.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Получить текущего авторизованного пользователя."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )
