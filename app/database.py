# Импорт функций для работы с базой данных
from sqlalchemy import create_engine  # Создаёт подключение к СУБД
from sqlalchemy.ext.declarative import declarative_base  # Базовый класс
from sqlalchemy.orm import sessionmaker  # Фабрика сессий для запросов к БД
import os  # Работа с переменными окружения
from dotenv import load_dotenv  # Загрузка переменных из .env файла

# Загружаем переменные окружения из файла .env (если он существует)
load_dotenv()

# Получаем строку подключения из .env, если нет — используем значение
# по умолчанию
# Формат: postgresql://пользователь:пароль@хост:порт/имя_базы
DATABASE_URL = os.getenv(
    "DATABASE_URL",  # Ключ в .env файле
    "postgresql://username:password@localhost/spellcheck_db"
)  # Значение по умолчанию (замените на своё!)

# Создаём "движок" — объект для подключения к PostgreSQL
engine = create_engine(
    DATABASE_URL,  # Строка подключения
    echo=True  # True = выводить все SQL-запросы в консоль (для отладки)
)

# Создаём фабрику сессий — объект, который будет создавать сессии
# для работы с БД
SessionLocal = sessionmaker(
    autocommit=False,  # Отключаем автокоммит
    autoflush=False,  # Отключаем авто-сброс буфера
    bind=engine  # Привязываем сессию к движку
)

# Создаём базовый класс для всех моделей (таблиц)
# Все классы-модели будут наследоваться от этого класса
Base = declarative_base()


# Dependency-функция для FastAPI — автоматически открывает и закрывает сессию
def get_db():
    db = SessionLocal()  # Создаём новую сессию БД
    try:
        yield db  # Передаём сессию в обработчик запроса
    finally:
        db.close()  # Закрываем сессию после обработки запроса
