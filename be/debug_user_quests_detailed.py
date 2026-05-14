import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user_quest import UserQuest
from app.models.quest import Quest
from app.models.submission import Submission
from app.models.enums import UserQuestStatus

async def analyze_quests():
    async with AsyncSessionLocal() as session:
        print("[DATA SCAN] Current Active User Quests Stats:")
        stmt = select(UserQuest, Quest).join(Quest, UserQuest.quest_id == Quest.id)
        result = await session.execute(stmt)
        rows = result.all()
        
        if not rows:
            print("No user quests found at all.")
            return
            
        for uq, q in rows:
            print(f"\nQuest Name: '{q.title}'")
            print(f"Status: {uq.status}")
            
            # Check submissions for this specific user quest
            sub_stmt = select(Submission).where(Submission.user_quest_id == uq.id)
            subs = (await session.execute(sub_stmt)).scalars().all()
            
            if not subs:
                print("  -> No submissions linked.")
            else:
                print(f"  -> Found {len(subs)} submission(s):")
                for s in subs:
                    print(f"     - Sub ID: {str(s.id)[:8]}, Status: {s.status}, AI Score: {s.ai_score}")

if __name__ == "__main__":
    asyncio.run(analyze_quests())
