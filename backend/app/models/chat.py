"""Модель сообщения в чате для хранения истории переписки.

Содержит класс ChatMessage для хранения пар оригинальных и исправленных текстов.
"""

# Импорт компонентов SQLAlchemy
from sqlalchemy import (
    Column, Integer, Text, Boolean, DateTime, ForeignKey
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..databases.database import Base


# Модель сообщения в чате — хранит пары "оригинал → исправленный текст"
class ChatMessage(Base):
    """Модель сообщения в чате.
    
    Хранит пары оригинальных сообщений пользователя и исправленных текстов.
    
    Attributes:
        id: Первичный ключ сообщения.
        user_id: Внешний ключ пользователя.
        text: Текст сообщения.
        is_user_message: Флаг, указывающий, что сообщение от пользователя.
        created_at: Время создания сообщения.
        user: Связь с моделью пользователя.
    """
    __tablename__ = "chat_messages"  # Имя таблицы

    # Первичный ключ
    id = Column(Integer, primary_key=True, index=True)

    # Внешний ключ — ссылка на пользователя
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Текст сообщения — может быть длинным (используем Text)
    text = Column(Text, nullable=False)

    # Флаг: True = сообщение от пользователя (оригинал),
    # False = ответ системы (исправленный текст)
    is_user_message = Column(Boolean, nullable=False)

    # Время создания сообщения (с индексом для быстрого поиска)
    created_at = Column(DateTime(timezone=True), server_default=func.now(),
                        index=True)

    # Связь с пользователем — позволяет получить данные через .user
    user = relationship("User", backref="chat_messages")

    # Метод для отладки
    def __repr__(self):
        """Возвращает строковое представление сообщения для отладки.
        
        Returns:
            str: Строковое представление объекта ChatMessage.
        """
        return (
            f"<ChatMessage(id={self.id}, user_id={self.user_id}, "
            f"is_user={self.is_user_message})>"
        )

    # Преобразование в словарь для API
    def to_dict(self):
        """Преобразует сообщение в словарь для API ответа.
        
        Returns:
            dict: Словарь с данными сообщения.
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "text": self.text,
            "is_user_message": self.is_user_message,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at else None
            )
        }
