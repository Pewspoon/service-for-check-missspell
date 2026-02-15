"""Модуль для создания и управления таблицами базы данных.

Содержит функции для инициализации базы данных и получения сессий.
"""

# Импорт библиотеки для работы с PostgreSQL
from sqlmodel import create_engine, SQLModel, Session
import os
from dotenv import load_dotenv
from typing import Generator


# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем DATABASE_URL из переменных окружения
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@database:5432/database"
)

engine = create_engine(DATABASE_URL, echo=True)


def get_session() -> Generator[Session, None, None]:
    """Зависимость для получения сессии БД в FastAPI.
    
    Создаёт сессию базы данных и автоматически закрывает её после использования.
    
    Yields:
        Session: Сессия базы данных SQLModel.
    """
    with Session(engine) as session:
        yield session


def init_db():
    """Создаёт все таблицы в базе данных.
    
    Инициализирует структуру базы данных на основе определённых моделей SQLModel.
    """
    SQLModel.metadata.create_all(engine)


# Запуск функции при выполнении скрипта
if __name__ == "__main__":
    init_db()
