"""Клиент обращения к Ollama для выполнения ML-задачи воркера."""

import requests
import logging
import json
import os

# Константы
OLLAMA_URL = 'http://ollama:11434/api/generate'
DEFAULT_MODEL_NAME = os.getenv("OLLAMA_MODEL", "gemma3:1b")
NUM_PREDICT = 30  # количество токенов для предсказания
REQUEST_TIMEOUT = 10  # seconds

# Настраиваем общий уровень логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def _parse_response(response_text: str) -> str:
    """Парсит ответ от LLM модели."""
    full_response = ''
    for line in response_text.strip().split('\n'):
        if not line:
            continue
        try:
            response_obj = json.loads(line)
            if 'response' in response_obj:
                full_response += response_obj['response']
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON line: {e}")
    return full_response.strip()


def do_task(text: str, model_name: str | None = None) -> str:
    """
    Выполняет задачу обработки текста с помощью LLM.

    Args:
        text: Входящий текст для обработки

    Returns:
        str: Краткое продолжение текста (не более 10 токенов)
    """
    model_for_request = (model_name or DEFAULT_MODEL_NAME).strip()
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                'model': model_for_request,
                'prompt': text,
                'options': {
                    'num_predict': NUM_PREDICT
                }
            },
            timeout=REQUEST_TIMEOUT
        )

        logger.info(f"Response status code: {response.status_code}")
        logger.debug(f"Response content: {response.content}")

        if response.status_code == 404:
            if model_for_request != DEFAULT_MODEL_NAME:
                logger.warning(
                    "Model '%s' not found. Falling back to '%s'",
                    model_for_request,
                    DEFAULT_MODEL_NAME
                )
                return do_task(text, DEFAULT_MODEL_NAME)
            return (
                f'Модель "{model_for_request}" не найдена в Ollama. '
                'Проверьте OLLAMA_MODEL и docker-compose.'
            )

        if response.status_code == 200:
            return _parse_response(response.text)

        return f'Ошибка сервера: {response.status_code}'

    except requests.Timeout:
        logger.error("Request timed out")
        return 'Превышено время ожидания ответа'
    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        return 'Ошибка при выполнении запроса'
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 'Неожиданная ошибка при обработке'
