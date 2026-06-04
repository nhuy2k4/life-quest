import asyncio
import os

import asyncpg


async def main():
    database_url = os.environ["DATABASE_URL"].replace(
        "postgresql+asyncpg://",
        "postgresql://",
    )

    conn = await asyncpg.connect(database_url)
    await conn.execute(
        "ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)"
    )
    await conn.close()


asyncio.run(main())