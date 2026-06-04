from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, delete, func, select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.recommendation import RecommendationLog
from app.workers.celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(name="maintenance.reco_daily_stats")
def recompute_recommendation_stats(stat_date: str | None = None) -> None:
	"""Deprecated compatibility task.

	The MVP recommendation system now derives popularity directly from
	recommendation_logs/posts and no longer writes quest_stats_daily or
	trending_scores tables.
	"""
	asyncio.run(_log_recommendation_activity_summary(stat_date))


@celery.task(name="maintenance.reco_log_retention")
def prune_recommendation_logs() -> None:
	"""Delete old recommendation logs in small batches."""
	asyncio.run(_prune_recommendation_logs())


async def _log_recommendation_activity_summary(stat_date: str | None) -> None:
	cutoff = datetime.now(timezone.utc) - timedelta(days=1)
	async with AsyncSessionLocal() as session:
		stmt = (
			select(
				func.count().label("total"),
				func.sum(case((RecommendationLog.event == "shown", 1), else_=0)).label("shown"),
				func.sum(case((RecommendationLog.event == "clicked", 1), else_=0)).label("clicked"),
				func.sum(case((RecommendationLog.event == "started", 1), else_=0)).label("started"),
				func.sum(case((RecommendationLog.event == "completed", 1), else_=0)).label("completed"),
			)
			.select_from(RecommendationLog)
			.where(RecommendationLog.created_at >= cutoff)
		)
		total, shown, clicked, started, completed = (await session.execute(stmt)).one()
		logger.info(
			"Recommendation activity summary stat_date=%s total=%s shown=%s clicked=%s started=%s completed=%s",
			stat_date,
			int(total or 0),
			int(shown or 0),
			int(clicked or 0),
			int(started or 0),
			int(completed or 0),
		)


async def _prune_recommendation_logs() -> None:
	retention_days = max(int(settings.RECOMMENDATION_LOG_RETENTION_DAYS), 14)
	batch_size = max(int(settings.RECOMMENDATION_LOG_CLEANUP_BATCH_SIZE), 100)
	cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
	total_deleted = 0

	async with AsyncSessionLocal() as session:
		while True:
			old_ids = (
				select(RecommendationLog.id)
				.where(RecommendationLog.created_at < cutoff)
				.order_by(RecommendationLog.created_at.asc())
				.limit(batch_size)
			)
			result = await session.execute(delete(RecommendationLog).where(RecommendationLog.id.in_(old_ids)))
			deleted = int(result.rowcount or 0)
			await session.commit()
			total_deleted += deleted
			if deleted < batch_size:
				break

	logger.info(
		"Recommendation log retention complete retention_days=%s cutoff=%s deleted=%s",
		retention_days,
		cutoff.isoformat(),
		total_deleted,
	)
