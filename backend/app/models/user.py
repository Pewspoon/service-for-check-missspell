from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum
import re


if TYPE_CHECKING:
    from .event import Event


# Pydantic models
class UserRole(str, Enum):
    """Roles available for users in the system."""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class UserBase(SQLModel):
    """Base schema for user data shared across requests and DB models."""
    username: str = Field(index=True, unique=True, min_length=3, max_length=50)
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    role: UserRole = Field(default=UserRole.USER)


class BalanceBase(SQLModel):
    """Base schema for user balance values."""
    amount: float = Field(default=0.0, ge=0)


class TransactionBase(SQLModel):
    """Base schema for transaction payloads."""
    amount: float = Field(gt=0)
    type: str = Field(description="deposit, withdrawal")
    description: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str


class UserUpdate(SQLModel):
    """Schema for updating user fields."""
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction."""
    user_id: int


class MLModelBase(SQLModel):
    """Base schema with common fields for ML models."""
    name: str = Field(min_length=1, max_length=255)
    version: str = Field(default="1.0.0")
    description: Optional[str] = None


class MLModelCreate(MLModelBase):
    """Schema for creating an ML model via API request."""
    file_path: str


class MLModelRead(MLModelBase):
    """Schema for reading ML model data in API response."""
    id: int
    file_path: str
    created_at: datetime


class MLPredictionRequest(SQLModel):
    """Schema for ML prediction request payload."""
    text: str
    model_id: int
    user_id: int


class MLPredictionResponse(SQLModel):
    """Schema for ML prediction response data."""
    result: str
    model_name: str


# Database tables
class User(UserBase, table=True):
    """Database model for users."""
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    balance: Optional["Balance"] = Relationship(back_populates="user")
    transactions: List["Transaction"] = Relationship(back_populates="user")
    events: List["Event"] = Relationship(back_populates="creator")

    def __str__(self) -> str:
        """Return a human-readable representation of the user."""
        return f"Id: {self.id}. Email: {self.email}"

    class Config:
        """Pydantic model configuration for User."""
        validate_assignment = True
        arbitrary_types_allowed = True

    def validate_email(self) -> bool:
        """Validate user email and raise ValueError on failure."""
        pattern = re.compile(
            r"^(?!\.)[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\."
            r"[A-Za-z]{2,}$"
        )
        if not pattern.match(self.email):
            raise ValueError("Invalid email format")
        return True

    @property
    def event_count(self) -> int:
        """Return the number of events linked to the user."""
        return len(self.events)


class Balance(BalanceBase, table=True):
    """Database model for user balance."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    user: User = Relationship(back_populates="balance")
    amount_of_replenishment: Optional[int]


class Transaction(TransactionBase, table=True):
    """Database model for transactions."""
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="transactions")


class MLModel(MLModelBase, table=True):
    """Database model for ML models table."""
    id: Optional[int] = Field(default=None, primary_key=True)
    file_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: int = Field(foreign_key="user.id")


class MLPredictionHistory(SQLModel, table=True):
    """Database model for ML prediction history."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    model_id: int = Field(foreign_key="mlmodel.id")
    input_text: str
    result: str
    cost: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MLPredictionHistoryRead(SQLModel):
    """Schema for reading ML prediction history."""
    id: int
    user_id: int
    model_id: int
    input_text: str
    result: str
    cost: float
    created_at: datetime


