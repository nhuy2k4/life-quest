import argparse
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import delete, func, select

# Ensure project root is on sys.path when running as a script.
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.models.enums import UserRole
from app.models.user import User


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Delete users created within the last N minutes.")
    parser.add_argument("--minutes", type=int, default=15, help="Lookback window in minutes.")
    return parser.parse_args()


async def purge_recent_users(minutes: int) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    async with AsyncSessionLocal() as session:
        total = await session.scalar(
            select(func.count()).select_from(User).where(
                User.created_at >= cutoff,
                User.role == UserRole.USER,
            )
        )
        count = int(total or 0)
        if count == 0:
            return 0
        await session.execute(
            delete(User).where(
                User.created_at >= cutoff,
                User.role == UserRole.USER,
            )
        )
        await session.commit()
        return count


def main() -> None:
    args = parse_args()
    deleted = asyncio.run(purge_recent_users(args.minutes))
    print(f"[OK] Deleted {deleted} users created in the last {args.minutes} minutes (role=user).")


if __name__ == "__main__":
    main()
