# Импорт библиотеки для работы с PostgreSQL
from sqlmodel import create_engine, SQLModel
import os
from dotenv import load_dotenv


# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем DATABASE_URL из переменных окружения
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@database:5432/database"
)

engine = create_engine(DATABASE_URL)


def create_db_tables():
    """Создаёт все таблицы в базе данных"""
    SQLModel.metadata.create_all(engine)


# Запуск функции при выполнении скрипта
if __name__ == "__main__":
    create_db_tables()
