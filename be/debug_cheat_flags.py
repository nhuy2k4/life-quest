import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.submission import Submission

async def check_cheat_flags():
    async with AsyncSessionLocal() as session:
        stmt = select(Submission).where(Submission.status == 'manual_review')
        result = await session.execute(stmt)
        s = result.scalars().first()
        if s:
            print(f"\n--- DEBUG SUBMISSION {s.id} ---")
            print(f"Status: {s.status}")
            print(f"AI Score: {s.ai_score}")
            print(f"Is Suspicious: {s.is_suspicious}")
            import json
            print(f"Cheat Flags:\n{json.dumps(s.cheat_flags, indent=2)}")
            print(f"AI Metadata:\n{json.dumps(s.ai_metadata, indent=2)}")
        else:
            print("No submission in manual_review found.")

if __name__ == "__main__":
    asyncio.run(check_cheat_flags())
