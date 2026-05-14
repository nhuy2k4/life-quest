from fastapi import APIRouter

from app.api.v1 import admin, auth, gamification, notifications, pois, quests, recommendations, social, submissions, uploads, users

api_router = APIRouter(prefix="/api/v1")

# ── Auth ──────────────────────────────────────────────────────────────────────
api_router.include_router(auth.router)

# ── Sẽ thêm dần khi implement các module khác ─────────────────────────────────
api_router.include_router(users.router)
api_router.include_router(quests.router)
api_router.include_router(pois.router)
api_router.include_router(submissions.router)
api_router.include_router(recommendations.router)
api_router.include_router(social.router)
api_router.include_router(admin.router)
api_router.include_router(gamification.router)
api_router.include_router(uploads.router)
api_router.include_router(notifications.router)
