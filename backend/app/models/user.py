from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum
import re


if TYPE_CHECKING:
    from .event import Event


# Pydantic models
class UserRole(str, Enum):
    """Роли, доступные пользователям в системе."""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class UserBase(SQLModel):
    """Базовая схема данных пользователя, общая для запросов и моделей БД."""
    username: str = Field(index=True, unique=True, min_length=3, max_length=50)
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    role: UserRole = Field(default=UserRole.USER)


class BalanceBase(SQLModel):
    """Базовая схема для значений баланса пользователя."""
    amount: float = Field(default=0.0, ge=0)


class TransactionBase(SQLModel):
    """Базовая схема для данных транзакций."""
    amount: float = Field(gt=0)
    type: str = Field(description="deposit, withdrawal")
    description: Optional[str] = None


class UserCreate(UserBase):
    """Схема для создания нового пользователя."""
    password: str


class UserUpdate(SQLModel):
    """Схема для обновления полей пользователя."""
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class TransactionCreate(TransactionBase):
    """Схема для создания транзакции."""
    user_id: int


class MLModelBase(SQLModel):
    """Базовая схема с общими полями для ML-моделей."""
    name: str = Field(min_length=1, max_length=255)
    version: str = Field(default="1.0.0")
    description: Optional[str] = None


class MLModelCreate(MLModelBase):
    """Схема для создания ML-модели через API-запрос."""
    file_path: str


class MLModelRead(MLModelBase):
    """Схема для чтения данных ML-модели в ответе API."""
    id: int
    file_path: str
    created_at: datetime


class MLPredictionRequest(SQLModel):
    """Схема для запроса ML-предсказания."""
    text: str
    model_id: int
    user_id: Optional[int] = None


class MLPredictionResponse(SQLModel):
    """Схема для данных ответа ML-предсказания."""
    result: str
    model_name: str


class MLPredictionHistoryRead(SQLModel):
    """Схема для чтения истории ML-предсказаний."""
    id: int
    user_id: int
    model_id: int
    input_text: str
    result: str
    cost: float
    created_at: datetime


class TaskResultRequest(SQLModel):
    """Схема для получения результата от ML-воркера."""
    task_id: str
    prediction: str
    worker_id: str
    status: str = "completed"


# ============ User Response Schema (без пароля!) ============

class UserResponse(SQLModel):
    """Схема вывода данных пользователя (без пароля)."""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ Auth Schemas ============

class UserLoginRequest(SQLModel):
    """Схема ввода для входа пользователя (устаревший эндпоинт)."""
    email: str
    password: str


class TokenResponse(SQLModel):
    """Схема вывода для ответа с JWT-токеном."""
    access_token: str
    token_type: str = "bearer"


class AuthorizationResponse(SQLModel):
    """Схема вывода для устаревшего эндпоинта авторизации."""
    username: str
    message: str


# ============ Balance Schemas ============

class BalanceResponse(SQLModel):
    """Схема вывода для баланса пользователя."""
    user_id: int
    amount: float = Field(..., ge=0)


class BalanceReplenishRequest(SQLModel):
    """Схема ввода для пополнения баланса."""
    amount: float = Field(..., gt=0, description="Amount to replenish")


# ============ Transaction Schemas ============

class TransactionResponse(SQLModel):
    """Схема вывода для данных транзакции."""
    id: int
    user_id: int
    amount: float
    type: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============ ML History Schemas ============

class MLHistoryCreateRequest(SQLModel):
    """Схема ввода для создания записи истории ML-предсказаний."""
    model_id: int
    input_text: str
    result: str
    cost: float = Field(..., ge=0)


# ============ Event Schemas ============

class EventResponse(SQLModel):
    """Схема вывода для данных события."""
    id: int
    title: str
    image: str
    description: str
    creator_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Chat Schemas ============

class ChatMessageCreate(SQLModel):
    """Схема ввода для создания сообщения в чате."""
    text: str


class ChatMessageResponse(SQLModel):
    """Схема вывода для данных сообщения в чате."""
    id: int
    user_id: int
    text: str
    is_user_message: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Database tables
class User(UserBase, table=True):
    """Модель базы данных для пользователей."""
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    balance: Optional["Balance"] = Relationship(back_populates="user")
    transactions: List["Transaction"] = Relationship(back_populates="user")
    events: List["Event"] = Relationship(back_populates="creator")

    def __str__(self) -> str:
        """Возвращает человекочитаемое представление пользователя."""
        return f"Id: {self.id}. Email: {self.email}"

    class Config:
        """Конфигурация модели Pydantic для User."""
        validate_assignment = True
        arbitrary_types_allowed = True

    def validate_email(self) -> bool:
        """Проверяет email пользователя и вызывает ValueError при неудаче."""
        pattern = re.compile(
            r"^(?!\.)[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\."
            r"[A-Za-z]{2,}$"
        )
        if not pattern.match(self.email):
            raise ValueError("Invalid email format")
        return True

    @property
    def event_count(self) -> int:
        """Возвращает количество событий, связанных с пользователем."""
        return len(self.events)


class Balance(BalanceBase, table=True):
    """Модель базы данных для баланса пользователя."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    user: User = Relationship(back_populates="balance")
    amount_of_replenishment: Optional[int]


class Transaction(TransactionBase, table=True):
    """Модель базы данных для транзакций."""
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="transactions")


class MLModel(MLModelBase, table=True):
    """Модель базы данных для таблицы ML-моделей."""
    id: Optional[int] = Field(default=None, primary_key=True)
    file_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: int = Field(foreign_key="user.id")


class MLPredictionHistory(SQLModel, table=True):
    """Модель базы данных для истории ML-предсказаний."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    model_id: int = Field(foreign_key="mlmodel.id")
    input_text: str
    result: str
    cost: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    task_id: Optional[str] = Field(default=None, index=True)  # новое поле


