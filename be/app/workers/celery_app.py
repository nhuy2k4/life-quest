from __future__ import annotations

from urllib.parse import urlparse, urlunparse

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings


def _redis_db_url(base_url: str, db_index: int) -> str:
	parsed = urlparse(base_url)
	path = f"/{db_index}"
	return urlunparse(parsed._replace(path=path))


redis_base = settings.REDIS_URL
broker_url = _redis_db_url(redis_base, 1)
result_backend = _redis_db_url(redis_base, 2)

celery = Celery(
	"lifequest",
	broker=broker_url,
	backend=result_backend,
	include=["app.workers.approval_tasks", "app.workers.maintenance_tasks"],
)

celery.conf.update(
	task_track_started=True,
	task_serializer="json",
	accept_content=["json"],
	result_serializer="json",
	timezone="UTC",
	enable_utc=True,
)

if not settings.TESTING:
	celery.conf.beat_schedule = {
		"reco_daily_stats": {
			"task": "maintenance.reco_daily_stats",
			"schedule": crontab(minute=10, hour=0),
		},
		"reco_trending_scores_7d": {
			"task": "maintenance.reco_trending_scores",
			"schedule": crontab(minute=20, hour=0),
			"args": ("7d",),
		},
	}
