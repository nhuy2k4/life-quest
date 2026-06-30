import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.audit import AiDetectionLog
from app.models.submission import Submission

async def main():
    async with AsyncSessionLocal() as session:
        # Get the 5 latest AI detection logs
        stmt = select(AiDetectionLog).order_by(AiDetectionLog.created_at.desc()).limit(5)
        logs = (await session.scalars(stmt)).all()
        for idx, log in enumerate(logs):
            print(f"--- LOG {idx+1} ---")
            print(f"Submission ID: {log.submission_id}")
            print(f"Labels returned: {log.labels}")
            
            # Fetch the associated quest labels
            sub_stmt = select(Submission).where(Submission.id == log.submission_id)
            sub = await session.scalar(sub_stmt)
            if sub and sub.user_quest:
                q = sub.user_quest.quest
                print(f"Quest Title: {q.title}")
                print(f"Quest Allowed Labels: {q.labels}")
                print(f"Quest Label Rules: {q.label_rules}")
                print(f"Submission status: {sub.status}")
                if sub.ai_metadata:
                    print(f"AI metadata: {sub.ai_metadata}")
            print()

if __name__ == "__main__":
    asyncio.run(main())
