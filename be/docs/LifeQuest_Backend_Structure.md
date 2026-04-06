# LifeQuest Backend — Cấu trúc thư mục

> Stack: **FastAPI + Python 3.11 · PostgreSQL + Redis · Celery · SQLAlchemy 2.0 · Alembic**

---

```
lifequest-backend/
│
├── app/
│   │
│   ├── main.py                        # Khởi động FastAPI, mount routers & middleware
│   │
│   ├── api/
│   │   ├── v1/
│   │   │   ├── router.py              # Gộp tất cả user routers
│   │   │   ├── auth.py                # POST /auth/register, login, refresh, logout
│   │   │   ├── users.py               # GET/PATCH /users/me, preferences
│   │   │   ├── quests.py              # GET list/detail, POST start, submit, history
│   │   │   ├── submissions.py         # GET /submissions/{id} — user xem của mình
│   │   │   ├── social.py              # feed, follow, like, comment
│   │   │   ├── gamification.py        # badges, xp-history
│   │   │   ├── recommendations.py     # GET /recommendations/quests (cache Redis 10p)
│   │   │   └── notifications.py       # GET list, PATCH mark-read
│   │   │
│   │   └── admin/
│   │       ├── quests.py              # CRUD quest + category
│   │       ├── submissions.py         # queue pending, approve, manual review
│   │       ├── users.py               # list, ban/unban, đổi role
│   │       ├── badges.py              # CRUD badge, grant thủ công
│   │       └── stats.py               # dashboard, audit log XP
│   │
│   ├── deps/
│   │   ├── auth.py                    # get_current_user(), require_admin()
│   │   └── db.py                      # get_db() — SQLAlchemy session dependency
│   │
│   ├── services/
│   │   ├── auth_service.py            # register (bcrypt), login (JWT), refresh, logout
│   │   ├── preference_service.py      # lưu interests, set onboarding_completed, invalidate cache
│   │   ├── quest_service.py           # start quest, submit (anti-cheat → upload → queue)
│   │   ├── submission_service.py      # approve, manual_review, pending queue
│   │   ├── ai_approval_service.py     # Google Vision API + rule-based, tính trust_score
│   │   ├── recommendation_service.py  # scoring 6 yếu tố + cache Redis 10 phút
│   │   ├── xp_service.py              # cấp XP idempotent (check submission_id trước)
│   │   ├── badge_service.py           # kiểm tra criteria JSONB, trao badge
│   │   ├── upload_service.py          # validate, MD5 hash, EXIF extract, upload Cloudinary
│   │   ├── social_service.py          # feed query, follow/unfollow, like toggle, comment CRUD
│   │   ├── notification_service.py    # tạo notification, đọc unread
│   │   └── admin_service.py           # dashboard stats, ban user, đổi role, export XP audit
│   │
│   ├── models/
│   │   ├── base.py                    # UUIDMixin, TimestampMixin (created_at, updated_at)
│   │   ├── auth.py                    # refresh_tokens, levels
│   │   ├── user.py                    # users
│   │   ├── user_preference.py         # user_preferences
│   │   ├── quest.py                   # quests, categories, quest_categories (M:N)
│   │   ├── user_quest.py              # user_quests (status machine)
│   │   ├── submission.py              # submissions (ảnh proof + anti-cheat)
│   │   ├── badge.py                   # badges, user_badges
│   │   ├── xp_transaction.py          # xp_transactions (audit log bất biến)
│   │   ├── social.py                  # follows, posts, likes, comments
│   │   └── notification.py            # notifications
│   │
│   ├── schemas/
│   │   ├── auth.py                    # RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
│   │   ├── user.py                    # UserMeResponse, UserPublicResponse, UpdateProfileRequest
│   │   ├── preference.py              # PreferenceRequest, PreferenceResponse
│   │   ├── quest.py                   # QuestResponse, QuestListResponse, StartQuestResponse
│   │   ├── submission.py              # SubmitProofRequest, SubmissionResponse
│   │   ├── social.py                  # FeedItem, PostResponse, CommentResponse
│   │   ├── gamification.py            # BadgeResponse, XpHistoryItem, LevelResponse
│   │   ├── admin.py                   # AdminUserResponse, DashboardStatsResponse
│   │   └── common.py                  # PaginatedResponse, ErrorResponse
│   │
│   ├── core/
│   │   ├── config.py                  # Settings (pydantic-settings) đọc .env — fail fast nếu thiếu
│   │   ├── security.py                # JWT encode/decode, bcrypt, token blacklist Redis
│   │   ├── database.py                # SQLAlchemy async engine + session factory
│   │   ├── redis.py                   # Redis client + helper (get/set/delete/cache)
│   │   └── exceptions.py             # Custom HTTP exceptions (NotFound, Forbidden, Conflict...)
│   │
│   └── middleware/
│       ├── cors.py                    # CORSMiddleware config
│       ├── rate_limit.py              # Rate limiting qua Redis
│       ├── logging.py                 # Request/response logging
│       └── error_handler.py           # Global exception handler → chuẩn ErrorResponse
│
├── workers/
│   ├── celery_app.py                  # Celery instance, Redis broker (DB1), result (DB2), beat schedule
│   ├── approval_tasks.py              # AI Vision deep check, retry 3 lần, idempotent
│   ├── reward_tasks.py                # XP → level → badge → tạo post → notification
│   ├── notification_tasks.py          # Push FCM, bulk notify, alert quest sắp hết hạn
│   └── maintenance_tasks.py           # Cron: expire quests (1h), leaderboard (5m), dọn tokens (daily), recalc weights (weekly)
│
├── migrations/
│   ├── env.py                         # Alembic env config
│   ├── script.py.mako
│   └── versions/                      # Alembic migration files
│       └── 001_initial_schema.py
│
├── tests/
│   ├── test_auth.py
│   ├── test_quests.py
│   ├── test_submissions.py
│   └── test_social.py
│
├── .env                               # KHÔNG commit — copy từ .env.example
├── .env.example                       # Template: DB_URL, REDIS_URL, JWT_SECRET, CLOUDINARY_*, GOOGLE_VISION_KEY
├── alembic.ini
├── pyproject.toml                     # Dependencies
└── README.md
```

---

## Thứ tự làm để chạy được

| Bước | Phần | Files |
|------|------|-------|
| 1 | Config & DB connect | `core/config.py`, `core/database.py`, `core/redis.py` |
| 2 | Models & Migration | `models/*.py` → alembic migrate → seed `levels`, `categories` |
| 3 | Core security | `core/security.py`, `deps/auth.py`, `deps/db.py` |
| 4 | Schemas | `schemas/*.py` |
| 5 | Auth service + router | `services/auth_service.py`, `api/v1/auth.py` |
| 6 | main.py | Mount routers, middleware, exception handler |
| 7 | Các services còn lại | Theo thứ tự: preference → upload → quest → xp → badge → social |
| 8 | Celery workers | `workers/celery_app.py` → approval → reward → maintenance |

---

## Quy tắc kiến trúc (từ TechRef)

- Luồng 1 chiều: `Router → Service → Model → DB` — không gọi ngược
- Router **không** tự query DB, chỉ gọi service
- XP **chỉ** cấp qua `xp_service` — đảm bảo idempotency
- Mọi thay đổi XP phải có `XpTransaction` record
- **Không bao giờ** auto-reject submission — chỉ `approved` hoặc `manual_review`
- Admin endpoints **bắt buộc** có `require_admin()` dependency
- Celery task phải idempotent — retry an toàn
- `onboarding_completed=false` → chặn truy cập quest endpoints
- Không commit `.env` vào git
