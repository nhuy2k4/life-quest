import asyncio
import uuid
from sqlalchemy import select
from app.core.database import async_session_maker
from app.models.event import Event, EventQuest
from app.models.enums import EventStatus
from datetime import datetime, timezone

async def test_query():
    async with async_session_maker() as session:
        now = datetime.now(timezone.utc)
        result = await session.execute(
            select(Event.id, EventQuest.quest_id, Event.status)
            .join(EventQuest, EventQuest.event_id == Event.id)
        )
        print("All Events with Quests:", result.all())

        # Let's test the specific query
        result = await session.execute(
            select(Event.id)
            .join(EventQuest, EventQuest.event_id == Event.id)
            .where(
                Event.status == EventStatus.ACTIVE,
                Event.start_at <= now,
                Event.end_at >= now,
            )
        )
        print("Active event ids:", result.scalars().all())

asyncio.run(test_query())
