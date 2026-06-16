import asyncio
import sys
from sqlalchemy import text
from app.core.database import engine

async def reset_all_users():
    print("--- STARTING MASSIVE ALL-USERS DATA RESET ---")
    print("WARNING: This will completely erase all user accounts and all user-generated data (posts, comments, chat history, XP, notifications, preferences, etc.).")
    
    # Check for confirmation
    if "--yes" not in sys.argv:
        print("[ABORTED] Please run the script with '--yes' to confirm execution.")
        print("Example: python admin_reset_all_users.py --yes")
        return

    # Tables to clear (in bottom-up order, though FK checks will be disabled for SQLite)
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
        "notifications",
        "user_preferences",
        "user_push_tokens",
        "users"
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
                print("[SUCCESS] All user accounts and dynamic user data successfully erased from SQLite!")
                
            else:
                # PostgreSQL
                print("Running TRUNCATE TABLE with CASCADE...")
                query = f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE;"
                await conn.execute(text(query))
                print("[SUCCESS] All user accounts and dynamic user data successfully erased from PostgreSQL!")

            print("\nInfrastructure and configuration (Quests, POIs, Levels, Categories) are preserved.")

        except Exception as e:
            print(f"[ERROR] Reset failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(reset_all_users())
