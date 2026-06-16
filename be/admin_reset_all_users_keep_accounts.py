import asyncio
import sys
from sqlalchemy import text, update
from app.core.database import engine
from app.models.user import User

async def reset_all_users_keep_accounts():
    print("--- STARTING MASSIVE DATA RESET (KEEPING ACCOUNTS) ---")
    print("WARNING: This will delete all posts, comments, likes, notifications, xp transactions, submissions, user quests, and chat messages for ALL users, but will KEEP the user accounts and preferences.")
    
    # Check for confirmation
    if "--yes" not in sys.argv:
        print("[ABORTED] Please run the script with '--yes' to confirm execution.")
        print("Example: python admin_reset_all_users_keep_accounts.py --yes")
        return

    # Tables to clear (excluding user accounts and preferences)
    tables = [
        "recommendation_logs",
        "ai_detection_logs",
        "audit_logs",
        "xp_transactions",
        "comments",
        "likes",
        "follows",
        "messages",
        "conversations",
        "event_results",
        "quest_instances",
        "posts",
        "user_badges",
        "submissions",
        "user_quests",
        "refresh_tokens",
        "notifications"
    ]

    async with engine.begin() as conn:
        try:
            dialect_name = conn.dialect.name
            print(f"Detected database dialect: {dialect_name}")

            if dialect_name == "sqlite":
                print("Disabling foreign keys temporarily (SQLite)...")
                await conn.execute(text("PRAGMA foreign_keys = OFF;"))
                
                for table in tables:
                    print(f"Deleting all rows from table: {table}...")
                    await conn.execute(text(f"DELETE FROM {table};"))
                    # Reset auto-increment sequence
                    try:
                        await conn.execute(text(f"DELETE FROM sqlite_sequence WHERE name = '{table}';"))
                    except Exception:
                        pass
                
                print("Re-enabling foreign keys (SQLite)...")
                await conn.execute(text("PRAGMA foreign_keys = ON;"))
                
            else:
                # PostgreSQL
                print("Running TRUNCATE TABLE with CASCADE...")
                query = f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE;"
                await conn.execute(text(query))

            # Reset progression columns on the users table
            print("Resetting all users progression metrics (XP, level, streak, trust score)...")
            await conn.execute(
                update(User)
                .values(
                    level_id=1,
                    xp=0,
                    streak_days=0,
                    trust_score=1.0
                )
            )

            print("[SUCCESS] All user dynamic data, progression, and social interactions successfully reset while keeping user accounts!")

        except Exception as e:
            print(f"[ERROR] Reset failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(reset_all_users_keep_accounts())
