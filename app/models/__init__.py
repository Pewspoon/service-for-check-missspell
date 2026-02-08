# Этот файл делает папку app/models пакетом Python
# и позволяет импортировать все модели одной строкой:
# from app.models import User

# Импортируем все модели, чтобы они были доступны извне пакета
from .user import (
    UserBase, UserCreate, UserRole, UserUpdate,
    BalanceBase, TransactionCreate, User, Transaction, Balance
)

# Список экспортируемых имён — что будет импортировано
# при from app.models import *
__all__ = [
    "UserRole", "UserBase", "UserCreate", "UserUpdate",
    "BalanceBase", "TransactionCreate", "User", "Balance", "Transaction"
]
