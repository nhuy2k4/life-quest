"""
Script: backfill_user_levels.py
Muc dich: Cap nhat level_id theo xp hien tai cho tat ca users.
Chay: python scripts/backfill_user_levels.py
"""
import asyncio
import sys
from pathlib import Path

# Them project root vao sys.path de import app.*
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.auth import Level
from app.models.user import User


def resolve_level_id(levels: list[Level], total_xp: int) -> int:
    level_id = levels[0].id
    for level in levels:
        if total_xp >= level.required_xp:
            level_id = level.id
        else:
            break
    return level_id


async def backfill_levels() -> None:
    async with AsyncSessionLocal() as session:
        levels = list(
            (await session.execute(select(Level).order_by(Level.required_xp.asc()))).scalars().all()
        )
        if not levels:
            print("[backfill] No levels found. Abort.")
            return

        users = list((await session.execute(select(User))).scalars().all())
        updated = 0

        for user in users:
            next_level_id = resolve_level_id(levels, user.xp)
            if user.level_id != next_level_id:
                user.level_id = next_level_id
                updated += 1

        if updated > 0:
            await session.commit()
        print(f"[backfill] Updated {updated}/{len(users)} users.")


if __name__ == "__main__":
    asyncio.run(backfill_levels())
