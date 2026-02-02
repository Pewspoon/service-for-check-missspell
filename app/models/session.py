# Импорт компонентов SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey  # Типы полей и внешний ключ
from sqlalchemy.sql import func                                      # Функции СУБД (например, NOW())
from sqlalchemy.orm import relationship                              # Связь между таблицами (1 ко многим)
from ..database import Base                                          # Базовый класс моделей
import secrets                                                       # Генерация криптографически стойких токенов

# Модель сессии — хранит активные сессии пользователей (вместо паролей)
class Session(Base):
    __tablename__ = "sessions"                                       # Имя таблицы

    # Уникальный идентификатор сессии — генерируется автоматически через secrets.token_hex(32)
    id = Column(String(64), primary_key=True, default=lambda: secrets.token_hex(32))

    # Внешний ключ — ссылка на пользователя (при удалении пользователя удаляются и его сессии)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Токен сессии — отправляется клиенту и используется для аутентификации в последующих запросах
    token = Column(String(128), unique=True, nullable=False, index=True)

    # Время истечения сессии — после этого времени токен становится не действительным.
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Время создания сессии
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связь "многие к одному" — объект сессии будет иметь атрибут .user с данными пользователя
    user = relationship("User", backref="sessions")                  # backref добавляет .sessions к объекту User

    # Метод для отладки
    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"

    # Преобразование в словарь для API
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "token": self.token,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
