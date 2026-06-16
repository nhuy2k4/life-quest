"""Celery tasks for event reward finalization."""
from __future__ import annotations

import asyncio
import logging

from app.core.database import AsyncSessionLocal
from app.workers.celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(name="events.finalize_overdue")
def finalize_overdue_events() -> None:
    """Finalize all active events whose end_at has passed and distribute rewards."""
    asyncio.run(_finalize_overdue_events_async())


async def _finalize_overdue_events_async() -> None:
    from app.services.event.event_service import EventService

    async with AsyncSessionLocal() as session:
        service = EventService(session)
        try:
            await service._finalize_overdue_events()
            logger.info("finalize_overdue_events: completed successfully")
        except Exception:
            logger.exception("finalize_overdue_events: unexpected error")
