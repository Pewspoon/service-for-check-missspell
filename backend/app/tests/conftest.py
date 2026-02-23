from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine


APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


# Чтобы `database.config.get_settings()` не падал при запуске pytest из корня репо.
os.environ.setdefault("DB_HOST", "test-db")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_USER", "test-user")
os.environ.setdefault("DB_PASS", "test-pass")
os.environ.setdefault("DB_NAME", "test-name")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")


@pytest.fixture()
def engine():
    # Регистрируем модели в metadata до create_all
    import models.user  # noqa: F401

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture()
def session(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture()
def user_factory(session):
    def _factory(
        *,
        username: str = "alice",
        email: str = "alice@example.com",
        password: str = "password",
        balance_amount: float | None = 100.0,
    ):
        from models.user import Balance, User, UserRole

        try:
            from auth import get_password_hash
            hashed_password = get_password_hash(password)
        except Exception:
            # Фикстура используется только там, где зависимости auth доступны.
            hashed_password = "test-hash"

        user = User(
            username=username,
            email=email,
            full_name=None,
            role=UserRole.USER,
            hashed_password=hashed_password,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        if balance_amount is not None:
            session.add(
                Balance(
                    user_id=user.id,
                    amount=balance_amount,
                    amount_of_replenishment=0,
                )
            )
            session.commit()

        return user

    return _factory


@pytest.fixture()
def ml_model_factory(session):
    def _factory(
        *,
        user_id: int,
        name: str = "test-model",
    ):
        from models.user import MLModel

        model = MLModel(
            name=name,
            version="1.0.0",
            description="test",
            file_path="/tmp/model",
            user_id=user_id,
        )
        session.add(model)
        session.commit()
        session.refresh(model)
        return model

    return _factory


@pytest.fixture()
def client(engine):
    pytest.importorskip("fastapi")
    pytest.importorskip("pika")

    from contextlib import asynccontextmanager
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from api import create_application
    from database.create_tables import get_session

    def override_get_session():
        with Session(engine) as test_session:
            yield test_session

    @asynccontextmanager
    async def no_lifespan(_: FastAPI):
        # Изолируем тесты от реального startup (Postgres/RabbitMQ init).
        yield

    app = create_application()
    app.dependency_overrides[get_session] = override_get_session
    app.router.lifespan_context = no_lifespan

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
