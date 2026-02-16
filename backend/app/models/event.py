"""Модель события в системе.

Содержит классы для создания, хранения и управления событиями.
"""

from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING


if TYPE_CHECKING:
    from .user import User


class EventBase(SQLModel):
    """Базовая модель события с общими полями.
    
    Attributes:
        title: Название события.
        image: URL или путь к изображению события.
        description: Описание события.
    """
    title: str = Field(..., min_length=1, max_length=100)
    image: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1, max_length=1000)


class Event(EventBase, table=True):
    """Модель события для хранения в базе данных.
    
    Представляет событие в системе с информацией о создателе.
    
    Attributes:
        id: Первичный ключ.
        creator_id: Внешний ключ к пользователю-создателю.
        creator: Связь с пользователем-создателем.
        created_at: Время создания события.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    creator_id: Optional[int] = Field(default=None, foreign_key="user.id")
    creator: Optional["User"] = Relationship(
        back_populates="events",
        sa_relationship_kwargs={"lazy": "selectin"}
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def __str__(self) -> str:
        """Возвращает строковое представление события.
        
        Returns:
            str: Строковое представление события.
        """
        creator = self.creator
        creator_email = creator.email if creator is not None else "n/a"
        return (
            f"Id: {self.id}. Title: {self.title}. "
            f"Creator: {creator_email}"
        )
    
    @property
    def short_description(self) -> str:
        """Возвращает сокращённое описание для предпросмотра.
        
        Returns:
            str: Описание, обрезанное до 100 символов.
        """
        max_length = 100
        return (
            f"{self.description[:max_length]}..."
            if len(self.description) > max_length
            else self.description
        )


class EventCreate(EventBase):
    """Схема для создания нового события."""
    pass


class EventUpdate(SQLModel):
    """Схема для обновления существующего события.
    
    Attributes:
        title: Новое название события (опционально).
        image: Новый URL изображения (опционально).
        description: Новое описание (опционально).
    """
    title: Optional[str] = None
    image: Optional[str] = None
    description: Optional[str] = None

    class Config:
        """Конфигурация модели."""
        validate_assignment = True
