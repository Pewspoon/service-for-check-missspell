# Инициализация базы данных
from .create_tables import engine, get_session, init_db

# Весь испорт при app.database import *
__all__ = ["engine", "get_session", "init_db"]
