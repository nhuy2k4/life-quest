from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import case, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.database import AsyncSessionLocal
from app.models.recommendation import RecommendationLog, QuestStatsDaily, TrendingScore
from app.workers.celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(name="maintenance.reco_daily_stats")
def recompute_recommendation_stats(stat_date: str | None = None) -> None:
	asyncio.run(_recompute_recommendation_stats(stat_date))


@celery.task(name="maintenance.reco_trending_scores")
def recompute_trending_scores(window: str = "7d") -> None:
	asyncio.run(_recompute_trending_scores(window))


async def _recompute_recommendation_stats(stat_date: str | None) -> None:
	if stat_date:
		try:
			stat_day = date.fromisoformat(stat_date)
		except ValueError:
			logger.warning("Invalid stat_date: %s", stat_date)
			return
	else:
		stat_day = datetime.now(timezone.utc).date()

	async with AsyncSessionLocal() as session:
		stmt = (
			select(
				RecommendationLog.quest_id,
				func.sum(case((RecommendationLog.event == "shown", 1), else_=0)).label("shown"),
				func.sum(case((RecommendationLog.event == "clicked", 1), else_=0)).label("clicked"),
				func.sum(case((RecommendationLog.event == "started", 1), else_=0)).label("started"),
				func.sum(case((RecommendationLog.event == "completed", 1), else_=0)).label("completed"),
				func.sum(case((RecommendationLog.event == "ignored", 1), else_=0)).label("ignored"),
			)
			.where(func.date(RecommendationLog.created_at) == stat_day)
			.group_by(RecommendationLog.quest_id)
		)

		rows = (await session.execute(stmt)).all()
		if not rows:
			return

		payloads: list[dict] = []
		for quest_id, shown, clicked, started, completed, ignored in rows:
			shown = int(shown or 0)
			clicked = int(clicked or 0)
			started = int(started or 0)
			completed = int(completed or 0)
			ignored = int(ignored or 0)

			completion_rate = (completed / started) if started > 0 else 0.0
			popularity_score = (clicked * 0.4) + (started * 0.6) + (completed * 1.0)

			payloads.append(
				{
					"id": uuid.uuid4(),
					"quest_id": quest_id,
					"stat_date": stat_day,
					"shown": shown,
					"clicked": clicked,
					"started": started,
					"completed": completed,
					"ignored": ignored,
					"completion_rate": completion_rate,
					"avg_completion_time_s": None,
					"popularity_score": popularity_score,
				}
			)

		insert_stmt = pg_insert(QuestStatsDaily).values(payloads)
		update_cols = {
			"shown": insert_stmt.excluded.shown,
			"clicked": insert_stmt.excluded.clicked,
			"started": insert_stmt.excluded.started,
			"completed": insert_stmt.excluded.completed,
			"ignored": insert_stmt.excluded.ignored,
			"completion_rate": insert_stmt.excluded.completion_rate,
			"avg_completion_time_s": insert_stmt.excluded.avg_completion_time_s,
			"popularity_score": insert_stmt.excluded.popularity_score,
		}
		await session.execute(
			insert_stmt.on_conflict_do_update(
				constraint="uq_quest_stats_daily_quest_date",
				set_=update_cols,
			)
		)
		await session.commit()


async def _recompute_trending_scores(window: str) -> None:
	if window != "7d":
		logger.warning("Unsupported trending window: %s", window)
		return

	cutoff = datetime.now(timezone.utc).date() - timedelta(days=6)
	async with AsyncSessionLocal() as session:
		stmt = (
			select(
				QuestStatsDaily.quest_id,
				func.sum(QuestStatsDaily.popularity_score).label("score"),
			)
			.where(QuestStatsDaily.stat_date >= cutoff)
			.group_by(QuestStatsDaily.quest_id)
		)
		rows = (await session.execute(stmt)).all()
		if not rows:
			return

		payloads = [
			{
				"id": uuid.uuid4(),
				"quest_id": quest_id,
				"window": window,
				"score": float(score or 0.0),
			}
			for quest_id, score in rows
		]

		insert_stmt = pg_insert(TrendingScore).values(payloads)
		await session.execute(
			insert_stmt.on_conflict_do_update(
				constraint="uq_trending_scores_quest_window",
				set_={
					"score": insert_stmt.excluded.score,
					"updated_at": func.now(),
				},
			)
		)
		await session.commit()
