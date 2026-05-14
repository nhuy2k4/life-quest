import asyncio
from sqlalchemy import select, delete
from app.core.database import AsyncSessionLocal
from app.models.submission import Submission
from app.models.user_quest import UserQuest

async def nuke_stuck_quests():
    async with AsyncSessionLocal() as session:
        print("[NUKE] Looking for submissions in manual_review to fully unlock user quests...")
        
        # Find user_quest_ids of submissions in manual review
        stmt = select(Submission.user_quest_id).where(Submission.status == 'manual_review')
        result = await session.execute(stmt)
        ids = [row[0] for row in result.all() if row[0] is not None]
        
        if not ids:
            print("[SAFE] No quests stuck in manual_review found.")
            return
            
        print(f"[INFO] Found {len(ids)} stuck user quests. Deleting them to completely restore availability...")
        
        # Delete the user quests
        await session.execute(delete(UserQuest).where(UserQuest.id.in_(ids)))
        
        # Commit changes
        await session.commit()
        print("[SUCCESS] Stuck quests have been successfully nuked and reset back to available pool.")

if __name__ == "__main__":
    asyncio.run(nuke_stuck_quests())
