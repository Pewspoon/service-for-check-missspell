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
    """Зависимость для получения сессии БД в FastAPI"""
    with Session(engine) as session:
        yield session


def init_db():
    """Создаёт все таблицы в базе данных"""
    SQLModel.metadata.create_all(engine)


# Запуск функции при выполнении скрипта
if __name__ == "__main__":
    init_db()
