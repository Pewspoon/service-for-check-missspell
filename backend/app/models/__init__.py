"""Пакет моделей и схем домена приложения.

Объединяет SQLModel-модели и pydantic-схемы в единую точку импорта.
"""

# Этот файл делает папку app/models пакетом Python
# и позволяет импортировать все модели одной строкой:
# from app.models import User

# Импортируем все модели, чтобы они были доступны извне пакета
from .user import (
    UserBase, UserCreate, UserRole, UserUpdate, UserResponse,
    UserLoginRequest, TokenResponse, AuthorizationResponse,
    BalanceBase, TransactionCreate, BalanceResponse, BalanceReplenishRequest,
    TransactionResponse, User, Transaction, Balance,
    MLModelBase, MLModelCreate, MLModelRead,
    MLPredictionRequest, MLPredictionResponse,
    MLPredictionHistoryRead, MLHistoryCreateRequest,
    EventResponse, ChatMessageCreate, ChatMessageResponse
)

# Список экспортируемых имён — что будет импортировано
# при from app.models import *
__all__ = [
    # User schemas
    "UserRole", "UserBase", "UserCreate", "UserUpdate", "UserResponse",
    "UserLoginRequest", "TokenResponse", "AuthorizationResponse",
    # Balance schemas
    "BalanceBase", "TransactionCreate", "BalanceResponse",
    "BalanceReplenishRequest", "TransactionResponse",
    # Database models
    "User", "Balance", "Transaction",
    # ML schemas
    "MLModelBase", "MLModelCreate", "MLModelRead",
    "MLPredictionRequest", "MLPredictionResponse",
    "MLPredictionHistoryRead", "MLHistoryCreateRequest",
    # Event & Chat schemas
    "EventResponse", "ChatMessageCreate", "ChatMessageResponse",
]
