from rmqconf import RabbitMQConfig
from worker import MLWorker
import sys
import pika
import time
import logging

# Настраиваем базовую конфигурацию логирования
logging.basicConfig(
    level=logging.DEBUG,  # Устанавливаем уровень логирования DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def run_worker(worker):
    """Запускает воркер с логикой переподключения."""
    while True:
        try:
            if not worker.connection or not worker.connection.is_open:
                logger.info("Connecting to RabbitMQ...")
                worker.connect()

            logger.info("Starting message consumption...")
            worker.start_consuming()

        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Connection error: {e}")
            logger.info("Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

        time.sleep(1)


def main():
    mode = 'ml'  # Режим ML для обработки задач
    logger.info(f"Starting worker in {mode} mode")

    worker = None
    try:
        config = RabbitMQConfig()
        worker = MLWorker(config)
        run_worker(worker)
    except Exception as e:
        logger.error(f"Application error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
