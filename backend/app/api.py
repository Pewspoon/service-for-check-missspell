from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.home import home_route
from routes.user import user_route
from routes.event import event_router
from routes.ml import ml_router
from database.create_tables import init_db
from database.config import get_settings
import uvicorn
import logging


logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Application startup completed successfully")
        yield
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise
    finally:
        logger.info("Application shutting down...")


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.API_VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
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
    app.include_router(user_route, prefix='/api/users', tags=['/auth'])
    app.include_router(user_route, prefix='/api/users', tags=['/auth'])
    app.include_router(event_router, prefix='/api/events', tags=['Events'])
    app.include_router(event_router, prefix='/health', tags=['health'])
    app.include_router(ml_router, tags=['ml'])
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
