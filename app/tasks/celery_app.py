from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "deribit",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.price_tasks"],
)

celery_app.conf.beat_schedule = {
    "fetch-prices-every-minute": {
        "task": "app.tasks.price_tasks.fetch_and_save_prices",
        "schedule": 60.0,
    },
}