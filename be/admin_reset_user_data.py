import asyncio
from sqlalchemy import text
from app.core.database import engine

async def reset_database():
    print("--- Starting massive User Data Reset ---")
    
    # Dùng CASCADE để Postgres tự động xóa sạch mọi ràng buộc liên quan
    tables = [
        "recommendation_logs",
        "ai_detection_logs",
        "audit_logs",
        "xp_transactions",
        "comments",
        "likes",
        "follows",
        "posts",
        "submissions",
        "user_quests",
        "refresh_tokens",
        "notifications",
        "user_preferences",
        "users"
    ]
    
    query = f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE;"
    
    async with engine.begin() as conn:
        try:
            print("Running TRUNCATE CASCADE...")
            await conn.execute(text(query))
            print("Cleanup SUCCESSFUL! All user dynamic data and transaction history erased.")
            print("System Infrastructure (Quests, POIs, Levels, Categories) has been preserved.")
        except Exception as e:
            print(f"Cleanup Failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(reset_database())
