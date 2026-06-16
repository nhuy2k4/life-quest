import asyncio
import sys
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def reset_user_data():
    print("=========================================================")
    print("WARNING: This script will delete ALL user-generated data:")
    print("- Submissions & Quest Instances")
    print("- Posts, Likes, Comments, and Follows")
    print("- Chat Conversations & Messages")
    print("- User Quests & User Badges")
    print("- Notifications & User Push Tokens")
    print("- XP Transactions & Recommendation logs")
    print("- Audit logs & AI detection logs")
    print("- Refresh tokens")
    print("---------------------------------------------------------")
    print("The tables 'users' and 'user_preferences' will be KEPT,")
    print("but all users' level, XP, and stats will be reset to defaults.")
    print("=========================================================")
    
    if len(sys.argv) < 2 or sys.argv[1] != "--yes":
        confirm = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            return

    queries = [
        # 1. Break cyclic dependency in conversations
        "UPDATE conversations SET last_message_id = NULL;",
        # 2. Delete chat messages & conversations
        "DELETE FROM messages;",
        "DELETE FROM conversations;",
        # 3. Delete notifications & push tokens
        "DELETE FROM notifications;",
        "DELETE FROM user_push_tokens;",
        # 4. Delete audit & recommendation logs
        "DELETE FROM audit_logs;",
        "DELETE FROM ai_detection_logs;",
        "DELETE FROM recommendation_logs;",
        # 5. Delete social interactions
        "DELETE FROM likes;",
        "DELETE FROM comments;",
        "DELETE FROM follows;",
        # 6. Delete event results
        "DELETE FROM event_results;",
        # 7. Delete posts
        "DELETE FROM posts;",
        # 8. Delete XP transactions first due to submissions foreign key dependency
        "DELETE FROM xp_transactions;",
        # 9. Delete submissions & quest instances
        "DELETE FROM quest_instances;",
        "DELETE FROM submissions;",
        # 10. Delete user quests
        "DELETE FROM user_quests;",
        # 11. Delete refresh tokens & user badges
        "DELETE FROM refresh_tokens;",
        "DELETE FROM user_badges;",
        # 12. Reset users levels & XP stats to default values
        "UPDATE users SET level_id = 1, xp = 0, streak_days = 0, trust_score = 1.0;"
    ]

    async with AsyncSessionLocal() as session:
        try:
            for query in queries:
                print(f"Executing: {query.strip()}")
                await session.execute(text(query))
            await session.commit()
            print("---------------------------------------------------------")
            print("✅ Successfully reset all user data while preserving 'users' and 'user_preferences'!")
        except Exception as e:
            await session.rollback()
            print(f"❌ Error during reset: {e}")

if __name__ == "__main__":
    asyncio.run(reset_user_data())
