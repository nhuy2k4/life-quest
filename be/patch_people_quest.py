import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.quest import Quest

async def patch_people_quest():
    async with AsyncSessionLocal() as session:
        # Fetch the People shot quest by ID
        stmt = select(Quest).where(Quest.id == 'a65f6494-33a0-413b-9f67-c89306f2b08d')
        result = await session.execute(stmt)
        q = result.scalars().first()
        if not q:
            # Fallback by title search
            stmt = select(Quest).where(Quest.title.ilike('%People shot%'))
            result = await session.execute(stmt)
            q = result.scalars().first()
            
        if not q:
            print("People shot Quest not found.")
            return
            
        print(f"\n--- Found Quest: {q.title} ---")
        print(f"Old Labels: {q.labels}")
        
        # Add new desk/work related labels
        new_labels = [
            "person", "people", "human", "face", "head", "portrait", 
            "man", "woman", "smile", "cheek", "chin", "forehead", 
            "nose", "lips", "eyebrow", "eyewear", "glasses", "selfie", 
            "hair", "hairstyle", "software engineering", "job", "office chair", 
            "desk", "personal computer", "electronic device", "furniture", 
            "peripheral", "computer desk", "computer monitor", "computer"
        ]
        
        # Keep old labels and merge with new ones (making sure everything is lowercase)
        current_labels = q.labels if q.labels else []
        combined = list(set([l.lower() for l in current_labels + new_labels]))
        
        # Define thresholds for all rules (defaulting to 0.5 for new ones, or keeping custom ones)
        rules = q.label_rules if q.label_rules else {}
        new_rules = {l: rules.get(l, 0.5) for l in combined}
        
        q.labels = combined
        q.label_rules = new_rules
        
        await session.commit()
        print(f"Success! Updated labels list: {q.labels}")

if __name__ == "__main__":
    asyncio.run(patch_people_quest())
