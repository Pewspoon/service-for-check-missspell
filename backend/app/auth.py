"""Модуль аутентификации и авторизации пользователей.

Содержит функции для хеширования паролей, создания и декодирования JWT токенов,
а также зависимости для получения текущего пользователя.
"""

from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from models.user import User
from database.create_tables import get_session
from database.config import get_settings

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль против хеша с использованием bcrypt.
    
    Args:
        plain_password: Пароль в открытом виде.
        hashed_password: Хешированный пароль.
    
    Returns:
        bool: True если пароль совпадает с хешем, иначе False.
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """Генерирует хеш из пароля с использованием bcrypt.
    
    Args:
        password: Пароль в открытом виде.
    
    Returns:
        str: Хешированный пароль.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """Создаёт JWT токен доступа.
    
    Args:
        data: Данные для кодирования в токен.
        expires_delta: Время жизни токена (опционально).
    
    Returns:
        str: Закодированный JWT токен.
    
    Raises:
        ValueError: Если SECRET_KEY не задан в настройках.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})

    # Проверяем, что SECRET_KEY вообще задан
    if settings.SECRET_KEY is None:
        raise ValueError(
            "SECRET_KEY не задан в настройках. Проверьте переменную окружения или .env файл."
        )

    # Приводим ключ к строке (если вдруг это SecretStr или другой объект)
    secret_key = str(settings.SECRET_KEY)

    # Кодируем токен
    encoded_jwt = jwt.encode(
        to_encode, secret_key, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Декодирует JWT токен.
    
    Args:
        token: JWT токен для декодирования.
    
    Returns:
        Optional[dict]: Декодированные данные из токена или None при ошибке.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    """Получает текущего пользователя из JWT токена.
    
    Извлекает и проверяет токен из заголовка Authorization,
    затем находит пользователя в базе данных.
    
    Args:
        token: JWT токен из заголовка Authorization.
        session: Сессия базы данных.
    
    Returns:
        User: Объект пользователя.
    
    Raises:
        HTTPException: Если учётные данные недействительны.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Получает текущего активного пользователя.
    
    Проверяет, что пользователь активен.
    
    Args:
        current_user: Текущий пользователь.
    
    Returns:
        User: Активный пользователь.
    
    Raises:
        HTTPException: Если пользователь неактивен.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
