"""Модуль конфигурации и создания FastAPI приложения.

Содержит функции для создания и настройки приложения FastAPI,
включая настройку CORS, маршрутизацию и управление жизненным циклом.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.home import home_route
from routes.user import user_route
from routes.event import event_router
from routes.balance import balance_of_user_route
from routes.ml import ml_router
from routes.history_of_ml_transaction import history_router
from database.create_tables import init_db, engine
from database.config import get_settings
from models.user import MLModel
from sqlmodel import Session, select
import uvicorn
import logging


logger = logging.getLogger(__name__)
settings = get_settings()


def create_default_ml_model():
    """Создаёт ML-модель по умолчанию, если она не существует."""
    with Session(engine) as session:
        existing = session.exec(
            select(MLModel).where(MLModel.name == "gemma3:270M-F16")
        ).first()
        if not existing:
            ml_model = MLModel(
                name="gemma3:270M-F16",
                version="1.0.0",
                description="Default ML model for text processing",
                file_path="/models/gemma3:270M-F16",
                user_id=1  # системный пользователь
            )
            session.add(ml_model)
            session.commit()
            logger.info("Default ML model created: gemma3:270M-F16")
        else:
            logger.info("ML model already exists: gemma3:270M-F16")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Контекстный менеджер жизненного цикла приложения.
    
    Выполняет инициализацию базы данных при запуске приложения
    и корректное завершение работы при остановке.
    
    Args:
        app: Экземпляр FastAPI приложения.
    
    Yields:
        None: Контроль передаётся основному приложению.
    
    Raises:
        Exception: Если инициализация базы данных не удалась.
    """
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Creating default ML model...")
        create_default_ml_model()
        logger.info("Application startup completed successfully")
        yield
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise
    finally:
        logger.info("Application shutting down...")


def create_application() -> FastAPI:
    """Создаёт и настраивает FastAPI приложение.
    
    Создаёт экземпляр FastAPI с настройками из конфигурации,
    добавляет CORS middleware и регистрирует все маршруты API.
    
    Returns:
        FastAPI: Сконфигурированный экземпляр приложения.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.API_VERSION,
        docs_url="/api/docs",           # теперь документация будет доступна по /api/docs
        openapi_url="/api/openapi.json", # и схема по /api/openapi.json
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(home_route, tags=['Home'])
    app.include_router(event_router, prefix='/api/events', tags=['Events'])
    app.include_router(event_router, prefix='/health', tags=['Health'])

    # /auth - registration and authentication
    app.include_router(user_route, prefix='/api/auth', tags=['/auth'])

    # /balance - balance operations
    app.include_router(balance_of_user_route, prefix='/api/balance', tags=['/balance'])

    # /predict - ML requests
    app.include_router(ml_router, prefix='/api/predict', tags=['/predict'])

    # /history - operation history
    app.include_router(history_router, prefix='/api/history', tags=['/history'])
    return app


app = create_application()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    uvicorn.run(
        'api:app',
        host='0.0.0.0',
        port=8080,
        reload=True,
        log_level="info"
    )
