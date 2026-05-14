# Next Steps Until Project Completion

## Backend

### 1) Recommendation (Finalize)

- Ensure cache invalidation strategy is finalized (Redis key naming, TTL tuning).
- Add tests for cache hit/miss and deterministic ordering.
- Add docs for /api/v1/recommendations/quests (request/response examples).

### 2) Gamification (Badges + XP History)

- Implement badge models/services (criteria evaluation, award logic).
- Add endpoints:
  - GET /api/v1/gamification/badges
  - GET /api/v1/gamification/badges/me
  - GET /api/v1/gamification/xp-history (already added; extend with filters if needed)
- Add tests for awarding badges and xp-history paging/filtering.

### 3) Social

- Implement social models (posts, follows, likes, comments).
- Add endpoints:
  - GET /api/v1/social/feed
  - POST /api/v1/social/follow/{id}
  - POST /api/v1/social/like/{id}
  - DELETE /api/v1/social/like/{id}
  - POST /api/v1/social/comment
- Ensure submission approval can create posts if required by product rules.
- Add tests for feed and interaction endpoints.

### 4) Notifications

- Implement notification service and API:
  - GET /api/v1/notifications
  - PATCH /api/v1/notifications/{id}/read
- Add tests for read/unread behavior.

### 5) Admin Panel (API)

- Implement admin CRUD endpoints for users, quests, submissions, badges, stats.
- Add role-based guards and audit log where needed.
- Add tests for admin-only access.

### 6) Observability and Stability

- Add structured logging for key workflows.
- Add error monitoring integration (Sentry or similar).
- Add rate-limit tuning for auth endpoints.

## Mobile

### 1) Onboarding

- Replace hardcoded interests with backend category IDs.
- Add activity level selection and send to /users/me/preferences.

### 2) Home / Recommendation

- Replace mock data with /recommendations/quests response.
- Add empty/loading/error states.

### 3) Quest Flow

- Wire quest list/detail to backend data.
- Hook start/submit to API:
  - POST /quests/{id}/start
  - POST /quests/{id}/submit

### 4) Profile / XP History

- Add XP history list view using /gamification/xp-history.
- Add badges view (when backend ready).

### 5) Social

- Replace mock feed with /social/feed.
- Implement like/comment/follow actions.

### 6) Notifications

- Connect notifications screen to /notifications endpoint.

### 7) Auth & Session

- Add refresh-token flow and auto-refresh on 401.
- Add logout action.

## QA / Release

### 1) Backend Test Coverage

- Run full pytest suite and fix any flakiness.
- Add integration tests for new endpoints.

### 2) Mobile E2E

- Run device/simulator smoke tests for:
  - login -> onboarding -> home
  - quest start -> submit -> admin approve
  - feed -> post detail -> profile

### 3) Documentation

- Update backend docs to reflect new endpoints.
- Replace mobile README with project-specific setup.

## Deployment

### 1) Backend

- Dockerize with env secrets and CI pipeline.
- Set up staging DB + Redis.

### 2) Mobile

- Configure Expo build profiles.
- Distribute staging build to testers.
