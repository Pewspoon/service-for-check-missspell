"""Модуль конфигурации приложения.

Содержит класс настроек приложения и базы данных,
а также функцию для получения экземпляра настроек.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Класс настроек приложения.
    
    Содержит конфигурацию базы данных, приложения и JWT токенов.
    Загружает значения из переменных окружения или файла .env.
    
    Attributes:
        DB_HOST: Хост базы данных.
        DB_PORT: Порт базы данных.
        DB_USER: Имя пользователя базы данных.
        DB_PASS: Пароль пользователя базы данных.
        DB_NAME: Название базы данных.
        APP_NAME: Название приложения.
        DEBUG: Режим отладки.
        API_VERSION: Версия API.
        APP_DESCRIPTION: Описание приложения.
        SECRET_KEY: Секретный ключ для JWT.
        ALGORITHM: Алгоритм шифрования JWT.
        ACCESS_TOKEN_EXPIRE_MINUTES: Время жизни токена в минутах.
    """
    
    # DataBase setting
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = None
    DB_USER: Optional[str] = None
    DB_PASS: Optional[str] = None
    DB_NAME: Optional[str] = None

    # Application settings
    APP_NAME: Optional[str] = None
    DEBUG: Optional[bool] = None
    API_VERSION: Optional[str] = None
    APP_DESCRIPTION: Optional[str] = None

    # JWT settings
    SECRET_KEY: Optional[str] = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @property
    def DATABASE_URL_asyncpg(self):
        """Возвращает URL для подключения к БД через asyncpg.
        
        Returns:
            str: Строка подключения к PostgreSQL через asyncpg.
        """
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def DATABASE_URL_psycopg(self):
        """Возвращает URL для подключения к БД через psycopg.
        
        Returns:
            str: Строка подключения к PostgreSQL через psycopg.
        """
        return (
            f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASS}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    def validate(self) -> None:
        """Проверяет наличие обязательных настроек базы данных.
        
        Raises:
            ValueError: Если отсутствуют обязательные настройки БД.
        """
        if not all([self.DB_HOST, self.DB_USER, self.DB_PASS, self.DB_NAME]):
            raise ValueError("Missing required database configuration")


@lru_cache
def get_settings() -> Settings:
    """Возвращает кэшированный экземпляр настроек приложения.
    
    Создаёт экземпляр Settings, проверяет его и кэширует результат.
    
    Returns:
        Settings: Экземпляр настроек приложения.
    """
    settings = Settings()
    settings.validate()
    return settings
