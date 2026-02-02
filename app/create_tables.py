# Импорт библиотеки для работы с PostgreSQL
import psycopg2  # Драйвер PostgreSQL
import os  # Для работы с переменными окружения
from dotenv import load_dotenv  # Загрузка .env файла

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем строку подключения к базе данных из .env
# Значение по умолчанию из вашего .env
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/misspell_db"
)

# Получаем время жизни сессии из .env (в секундах)
SESSION_EXPIRE_SECONDS = int(os.getenv("SESSION_EXPIRE_SECONDS", "86400"))


# Функция для создания таблиц через сырой SQL
def create_tables():
    """Создаёт все таблицы в базе данных с помощью чистого SQL"""

    # Устанавливаем подключение к базе данных
    conn = psycopg2.connect(DATABASE_URL)

    # Создаём курсор — объект для выполнения SQL-запросов
    cur = conn.cursor()

    try:
        print("Создание таблиц в базе данных...")
        print(f"Подключение к: {DATABASE_URL}")
        print(f"Время жизни сессии: {SESSION_EXPIRE_SECONDS} секунд "
              f"({SESSION_EXPIRE_SECONDS // 3600} часов)\n")

        # ============================================
        # Таблица пользователей (users)
        # ============================================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                balance INTEGER DEFAULT 10 NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP WITH TIME ZONE
            );
        """)
        print("✓ Таблица 'users' создана")

        # Создаём индексы для ускорения поиска
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);"
        )
        print("✓ Индексы для таблицы 'users' созданы")

        # ============================================
        # Таблица сессий (sessions)
        # ============================================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id VARCHAR(64) PRIMARY KEY DEFAULT
                    encode(gen_random_bytes(32), 'hex'),
                user_id INTEGER NOT NULL REFERENCES users(id)
                    ON DELETE CASCADE,
                token VARCHAR(128) UNIQUE NOT NULL,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✓ Таблица 'sessions' создана")

        # Индекс для поиска по токену
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);"
        )
        print("✓ Индекс для таблицы 'sessions' создан")

        # ============================================
        # Таблица сообщений чата (chat_messages)
        # ============================================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id)
                    ON DELETE CASCADE,
                text TEXT NOT NULL,
                is_user_message BOOLEAN NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✓ Таблица 'chat_messages' создана")

        # Индекс для поиска последних сообщений пользователя
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_user_created "
            "ON chat_messages(user_id, created_at DESC);"
        )
        print("✓ Индекс для таблицы 'chat_messages' создан")

        # ============================================
        # Таблица транзакций кредитов (credit_transactions)
        # ============================================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS credit_transactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id)
                    ON DELETE CASCADE,
                amount INTEGER NOT NULL,
                type VARCHAR(20) NOT NULL,
                description VARCHAR(200),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✓ Таблица 'credit_transactions' создана")

        # Индекс для поиска транзакций пользователя по времени
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_created "
            "ON credit_transactions(user_id, created_at DESC);"
        )
        print("✓ Индекс для таблицы 'credit_transactions' создан")

        # Фиксируем все изменения в базе данных
        conn.commit()

        print("\n" + "=" * 50)
        print("Все таблицы созданы успешно!")
        print("=" * 50)

    except Exception as e:
        # В случае ошибки откатываем все изменения
        conn.rollback()
        print(f"\nОшибка при создании таблиц: {e}")
        raise

    finally:
        # Закрываем курсор и подключение
        cur.close()
        conn.close()
        print("Подключение к базе данных закрыто.")


# Запуск функции при выполнении скрипта
if __name__ == "__main__":
    create_tables()
