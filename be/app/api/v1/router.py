from fastapi import APIRouter

from app.api.v1 import auth, quests, submissions, users

api_router = APIRouter(prefix="/api/v1")

# ── Auth ──────────────────────────────────────────────────────────────────────
api_router.include_router(auth.router)

# ── Sẽ thêm dần khi implement các module khác ─────────────────────────────────
api_router.include_router(users.router)
api_router.include_router(quests.router)
api_router.include_router(submissions.router)
# api_router.include_router(recommendations.router)
# api_router.include_router(social.router)
# api_router.include_router(gamification.router)
# api_router.include_router(notifications.router)
