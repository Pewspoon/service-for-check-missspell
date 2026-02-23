# Spellcheck Service

Веб-сервис с личным кабинетом для общения с LLM-моделью и хранения истории запросов.

## Что это

`Spellcheck Service` — это сайт-сервис, где пользователь:

- регистрируется и входит в личный кабинет;
- пополняет баланс;
- отправляет текст в модель;
- получает результат обработки;
- видит историю всех ML-запросов.

## Основные возможности

- Авторизация и регистрация (JWT).
- Личный кабинет пользователя.
- Баланс и списание стоимости ML-запроса.
- Асинхронная обработка задач через RabbitMQ + воркеры.
- Интеграция с Ollama для генерации ответа модели.
- История запросов и результатов в PostgreSQL.

## Технологии

- `FastAPI` — backend API.
- `Streamlit` — web-интерфейс (личный кабинет).
- `PostgreSQL` — хранение пользователей, баланса и истории.
- `RabbitMQ` — очередь задач.
- `Ollama` — LLM inference.
- `Docker Compose` — запуск всей системы.
- `Nginx` — входная точка веб-приложения.

## Архитектура

Высокоуровневый поток:

1. Пользователь открывает сайт через `Nginx`.
2. UI (`Streamlit`) отправляет запрос в `FastAPI`.
3. `FastAPI` публикует ML-задачу в `RabbitMQ`.
4. `ml_worker` забирает задачу и вызывает `Ollama`.
5. Результат возвращается в API и сохраняется в `PostgreSQL`.
6. Пользователь видит результат и историю в личном кабинете.

## Быстрый старт

### 1. Требования

- Docker Desktop (или Docker Engine + Compose plugin).

### 2. Запуск

Из папки `backend`:

```bash
cd backend
docker compose up --build
```

После старта:

- сайт: `http://localhost`
- API docs: `http://localhost/api/docs`
- RabbitMQ UI: `http://localhost:15672`

### 3. Остановка

```bash
docker compose down
```

## Переменные окружения

Файл: `backend/.env`.

Ключевые параметры:

- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `DATABASE_URL`
- `RABBITMQ_USER`, `RABBITMQ_PASSWORD`
- `SECRET_KEY`
- `OLLAMA_MODEL` (модель, которую подтягивает `ollama_init` и используют воркеры)

Пример:

```env
OLLAMA_MODEL=gemma3:1b
```

## Основные API-группы

- `/api/auth` — регистрация, вход, профиль.
- `/api/balance` — баланс и пополнение.
- `/api/predict` — запуск ML-задачи и получение результата.
- `/api/history` — история запросов пользователя.

## Структура проекта

```text
backend/
  app/            # FastAPI backend
  ml_worker/      # workers для обработки очереди
  streamlit/      # UI личного кабинета
  nginx/          # конфиг reverse proxy
  docker-compose.yaml
```

## Статус проекта

Учебный/демо-проект сервиса с личным кабинетом для общения с моделью.
