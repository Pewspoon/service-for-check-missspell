# Импорт компонентов SQLAlchemy для описания таблицы
from sqlalchemy import Column, Integer, String, DateTime, func  # Типы полей и функции СУБД
from ..database import Base                            # Базовый класс для моделей (из соседней папки)

# Определяем класс-модель, который будет соответствовать таблице в БД
class User(Base):
    __tablename__ = "users"                            # Имя таблицы в базе данных

    # Первичный ключ — уникальный идентификатор пользователя
    id = Column(Integer, primary_key=True, index=True)  # index=True ускоряет поиск по этому полю

    # Имя пользователя — уникальное, не может быть пустым
    username = Column(String(50), unique=True, nullable=False, index=True)

    # Email — тоже уникальный и обязательный
    email = Column(String(100), unique=True, nullable=False, index=True)

    # Баланс кредитов — целое число, по умолчанию 10 (начисляется при регистрации)
    balance = Column(Integer, default=10, nullable=False)

    # Дата и время создания аккаунта — автоматически заполняется СУБД текущим временем
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Дата последнего входа — может быть пустой (пока пользователь не входил)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Метод для удобного отображения объекта в консоли (отладка)
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', balance={self.balance})>"

    # Метод для преобразования объекта в словарь (удобно для отправки в JSON через API)
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "balance": self.balance,
            # Преобразуем datetime в строку формата ISO 8601 (например, "2024-01-15T10:30:00")
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }