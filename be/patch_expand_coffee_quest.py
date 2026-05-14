import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.quest import Quest

async def expand_coffee_quest_labels():
    async with AsyncSessionLocal() as session:
        print("[DB] Locating 'Coffee hunt' quest to broaden accepted labels...")
        
        stmt = select(Quest).where(Quest.title.ilike('%Coffee%'))
        result = await session.execute(stmt)
        quest = result.scalars().first()
        
        if not quest:
            print("[FAIL] Quest not found.")
            return
            
        print(f"Old Labels: {quest.labels}")
        print(f"Old Rules: {quest.label_rules}")
        
        # Adding Tableware, Cup, Mug, and broadening synonym lists
        new_labels = list(set(quest.labels + ['drink', 'tableware', 'cup', 'mug', 'beverage']))
        
        new_rules = quest.label_rules or {}
        new_rules.update({
            'Tableware': 0.6,
            'Cup': 0.6,
            'Mug': 0.6,
            'Drink': 0.6,
            'Drinkware': 0.6
        })
        
        from sqlalchemy.orm.attributes import flag_modified
        quest.labels = new_labels
        quest.label_rules = new_rules
        flag_modified(quest, "label_rules")
        flag_modified(quest, "labels")
        
        await session.commit()
        print("[SUCCESS] Expanded labels successfully!")
        print(f"New Labels: {quest.labels}")
        print(f"New Rules: {quest.label_rules}")

if __name__ == "__main__":
    asyncio.run(expand_coffee_quest_labels())
