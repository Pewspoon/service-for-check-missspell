# Импорт компонентов SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

# Модель транзакции — история списаний кредитов
class CreditTransaction(Base):
    __tablename__ = "credit_transactions"                            # Имя таблицы

    # Первичный ключ
    id = Column(Integer, primary_key=True, index=True)

    # Внешний ключ — ссылка на пользователя
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Сумма транзакции: отрицательная для списания (-1), положительная для пополнения (+10)
    amount = Column(Integer, nullable=False)

    # Тип операции: "debit" (списание) или "credit" (пополнение)
    type = Column(String(20), nullable=False)

    # Описание операции (например, "Исправление текста длиной 120 символов")
    description = Column(String(200), nullable=True)

    # Время создания транзакции
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Связь с пользователем
    user = relationship("User", backref="transactions")

    # Метод для отладки
    def __repr__(self):
        return f"<CreditTransaction(id={self.id}, user_id={self.user_id}, amount={self.amount})>"

    # Преобразование в словарь для API
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "type": self.type,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }