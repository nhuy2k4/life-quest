import asyncio
from app.core.database import engine
from sqlalchemy import text

async def patch_logs():
    async with engine.begin() as conn:
        print("Applying manual fix to recommendation_logs table...")
        await conn.execute(text("ALTER TABLE recommendation_logs ADD COLUMN IF NOT EXISTS features_snapshot JSON NULL"))
        await conn.execute(text("ALTER TABLE recommendation_logs ADD COLUMN IF NOT EXISTS rule_score FLOAT NULL"))
        await conn.execute(text("ALTER TABLE recommendation_logs ADD COLUMN IF NOT EXISTS ml_score FLOAT NULL"))
        await conn.execute(text("ALTER TABLE recommendation_logs ADD COLUMN IF NOT EXISTS final_score FLOAT NULL"))
        print("Columns patched successfully.")

if __name__ == "__main__":
    asyncio.run(patch_logs())
