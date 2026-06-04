from fastapi import APIRouter

from app.api.v1 import admin, auth, badges, categories, chat, events, gamification, notifications, pois, quests, recommendations, social, submissions, uploads, users

api_router = APIRouter(prefix="/api/v1")

# ── Auth ──────────────────────────────────────────────────────────────────────
api_router.include_router(auth.router)

# ── Sẽ thêm dần khi implement các module khác ─────────────────────────────────
api_router.include_router(users.router)
api_router.include_router(categories.router)
api_router.include_router(quests.router)
api_router.include_router(pois.router)
api_router.include_router(submissions.router)
api_router.include_router(recommendations.router)
api_router.include_router(social.router)
api_router.include_router(events.router)
api_router.include_router(chat.router)
api_router.include_router(admin.router)
api_router.include_router(gamification.router)
api_router.include_router(badges.router)
api_router.include_router(uploads.router)
api_router.include_router(notifications.router)
