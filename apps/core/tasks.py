from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task
def test_task():
    """테스트용 Celery 작업"""
    logger.info("Celery test task executed successfully!")
    return "Hello from Celery!"

@shared_task
def add(x, y):
    """간단한 덧셈 작업"""
    result = x + y
    logger.info(f"Celery add task: {x} + {y} = {result}")
    return result 