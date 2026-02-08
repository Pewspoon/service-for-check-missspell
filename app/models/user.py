from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum


# Pydantic модели
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class UserBase(SQLModel):
    username: str = Field(index=True, unique=True, min_length=3, max_length=50)
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    role: UserRole = Field(default=UserRole.USER)


class BalanceBase(SQLModel):
    amount: float = Field(default=0.0, ge=0)


class TransactionBase(SQLModel):
    amount: float = Field(gt=0)
    type: str = Field(description="deposit, withdrawal")
    description: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(SQLModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class TransactionCreate(TransactionBase):
    user_id: int


# Таблицы
class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    balance: Optional["Balance"] = Relationship(back_populates="user")
    transactions: List["Transaction"] = Relationship(back_populates="user")


class Balance(BalanceBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    user: User = Relationship(back_populates="balance")


class Transaction(TransactionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="transactions")
