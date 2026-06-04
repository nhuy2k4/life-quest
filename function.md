# Chuc nang va file lien quan

Ghi chu: Danh sach gom BE (FastAPI) va Mobile (React Native). Tap trung cac nhom chuc nang chinh va file core.

## 1) Auth & Session

BE:

- API: be/app/api/v1/auth.py
  - Chua cac route login/register/refresh/logout/otp.
  - Mapping request/response schema.
- Service: be/app/services/auth/
  - Xu ly logic dang nhap, refresh, logout.
  - Kiem tra user, ban/verify, tao token.
- Schema: be/app/schemas/auth.py
  - Dinh nghia request/response cho auth.
- Model: be/app/models/user.py, be/app/models/auth.py
  - users, refresh_tokens, levels.
- Deps: be/app/deps/auth.py
  - Lay current_user tu token.
- Middleware lien quan: be/app/middleware/ - Middleware lien quan auth/online tracking.
  Chuc nang chi tiet:
- Dang ky, dang nhap, dang xuat
- Google login
- Refresh token va xoay vong token
- OTP email: resend, verify, reset password
- Doi mat khau (user local)
  Mobile:
- Context: mobile/contexts/AuthContext.tsx
  - Luu auth state, hydrate, logout.
- Hook: mobile/hooks/useLogin.ts
  - Xu ly login local/google, luu token.
- Service: mobile/services/authService.ts
  - Goi API login/register/refresh.
- Storage: mobile/utils/storage.ts
  - Luu access/refresh token, onboarding.
- Screen: mobile/app/(auth)/, mobile/app/auth/ - Man hinh dang nhap/dang ky.
  Chuc nang chi tiet:
- Luu token, hydrate session
- Refresh token khi token het han
- Dang nhap username/password
- Dang nhap Google (Expo AuthSession)
- Dang xuat va xoa storage

## 2) User profile & settings

BE:

- API: be/app/api/v1/users.py
  - Route me/profile/update.
- Service: be/app/services/user/
  - Xu ly profile, update user.
- Schema: be/app/schemas/user.py, be/app/schemas/common.py
  - Dinh nghia response cho user.
- Model: be/app/models/user.py - Truong profile va thong tin user.
  Chuc nang chi tiet:
- Lay thong tin user (me, public profile)
- Cap nhat profile (display_name, bio, email)
- Trang thai khoa tai khoan
  Mobile:
- Context: mobile/contexts/UserContext.tsx
  - Luu currentUser, refresh data.
- Service: mobile/services/userService.ts
  - Goi API me, profile, update.
- Screens: mobile/app/(main)/other-profile/[id].tsx - UI xem profile nguoi khac.
  Chuc nang chi tiet:
- Fetch current user + profile
- Luu thong tin hien thi tren app

## 3) Onboarding & Preferences

BE:

- API: be/app/api/v1/categories.py, be/app/api/v1/users.py
  - Route list categories, save preferences.
- Service: be/app/services/user/preference_service.py, be/app/services/quest/
  - Luu/lay preference, cap nhat weights.
- Schema: be/app/schemas/preference.py, be/app/schemas/category.py
  - Dinh nghia payload preference.
- Model: be/app/models/user_preference.py, be/app/models/quest.py - user_preferences, categories.
  Chuc nang chi tiet:
- Danh sach categories
- Luu so thich ban dau
- Cap nhat interest_weights va muc do hoat dong
  Mobile:
- Screen: mobile/app/(onboarding)/
  - UI chon so thich.
- Service: mobile/services/categoryService.ts, mobile/services/preferenceService.ts - Goi API categories va save preferences.
  Chuc nang chi tiet:
- Chon so thich, gui len server
- Luu trang thai onboarding

## 4) Quest lifecycle

BE:

- API: be/app/api/v1/quests.py
  - Route list/start/detail quest.
- Service: be/app/services/quest/
  - Logic quest, start quest.
- Repo: be/app/repositories/quest_repository.py
  - Query quest, user_quest.
- Schema: be/app/schemas/quest.py
  - Request/response quest.
- Model: be/app/models/quest.py, be/app/models/user_quest.py - quest, user_quest, category link.
  Chuc nang chi tiet:
- Danh sach quest, chi tiet quest
- Start quest (tao user_quest)
- Het han quest theo time_limit
  Mobile:
- Screens: mobile/app/(main)/home.tsx, mobile/app/quest-detail.tsx
  - UI list quest, detail quest.
- Service: mobile/services/questService.ts - API list/start/detail.
  Chuc nang chi tiet:
- Hien thi danh sach quest va chi tiet
- Start quest, cap nhat trang thai

## 5) Submission & AI/vision

BE:

- API: be/app/api/v1/submissions.py, be/app/api/v1/uploads.py
  - Route submit/approve/reject, upload.
- Service: be/app/services/submission/, be/app/services/vision/, be/app/services/ai/
  - Xu ly submit, AI vision, cheat flags.
- Repo: be/app/repositories/submission_repository.py
  - Query submissions.
- Schema: be/app/schemas/submission.py, be/app/schemas/upload.py
  - Payload submit/upload.
- Model: be/app/models/submission.py, be/app/models/audit.py (ai_detection_logs) - submissions + log AI.
  Chuc nang chi tiet:
- Upload anh (signed/Cloudinary)
- Tao submission, luu metadata
- AI vision danh gia anh, log ket qua
- Duyet/tu choi submission
  Mobile:
- Service: mobile/services/uploadService.ts
  - Goi signed upload, upload file.
- Screens: mobile/app/quest-detail.tsx - UI chon anh, nop bai.
  Chuc nang chi tiet:
- Upload anh tu mobile
- Nop submission

## 6) Social (feed, post, comment, follow)

BE:

- API: be/app/api/v1/social.py
  - Route feed, like, comment, follow.
- Service: be/app/services/social/
  - Logic post, comment, follow.
- Schema: be/app/schemas/social.py
  - DTO social.
- Model: be/app/models/social.py - posts, likes, comments, follows.
  Chuc nang chi tiet:
- Feed (all/following)
- Like/unlike post
- Comment/reply
- Follow/unfollow user
- Tao/xoa post
  Mobile:
- Screens: mobile/app/(main)/home.tsx, mobile/app/post-detail.tsx
  - UI feed va chi tiet post.
- Service: mobile/services/socialService.ts
  - Goi API like, comment, follow.
- Components: mobile/components/lifequest/ - UI card/post/comment.
  Chuc nang chi tiet:
- Hien thi feed, post detail
- Tuong tac like/comment/follow

## 7) Notifications & Push

BE:

- API: be/app/api/v1/notifications.py
  - Route list, mark read, unread count.
- Service: be/app/services/notification/
  - Logic thong bao + push token.
- Schema: be/app/schemas/notification.py
  - DTO thong bao.
- Model: be/app/models/notification.py - notifications, user_push_tokens.
  Chuc nang chi tiet:
- Luu thong bao
- Danh dau da doc
- Dem so thong bao chua doc
- Dang ky push token
  Mobile:
- Context: mobile/contexts/ToastContext.tsx
  - Toast/alert UI.
- Screen: mobile/app/(main)/notifications.tsx
  - UI thong bao.
- Service: mobile/services/notificationService.ts - API thong bao + push token.
  Chuc nang chi tiet:
- Lay danh sach thong bao
- Danh dau da doc / doc tat ca
- Dang ky push token Expo/FCM

## 8) Recommendation

BE:

- API: be/app/api/v1/recommendations.py
  - Route recommend + log event.
- Service: be/app/services/recommendation/, be/app/services/pipeline/
  - Logic ranking + pipeline.
- Schema: be/app/schemas/recommendation.py
  - DTO recommendation.
- Model: be/app/models/recommendation.py - recommendation_logs, user_quest_stats.
  Chuc nang chi tiet:
- Goi y quest theo vi tri/so thich
- Log event (impression/click/start)
- Luu thong ke theo category
  Mobile:
- Service: mobile/services/recommendationService.ts
  - Goi API recommend + log event.
- Screens: mobile/app/(main)/home.tsx - UI goi y.
  Chuc nang chi tiet:
- Lay danh sach goi y
- Gui event log

## 9) POI (Point of Interest)

BE:

- API: be/app/api/v1/pois.py
  - Route search/list POI.
- Service: be/app/services/poi/
  - Logic POI + cache.
- Repo: be/app/repositories/poi_repository.py
  - Query POI.
- Schema: be/app/schemas/poi.py
  - DTO POI.
- Model: be/app/models/poi.py - Table pois.
  Chuc nang chi tiet:
- Quan ly POI
- Gan POI vao quest
- Search theo vi tri
  Mobile:
- Screen: mobile/app/(main)/home.tsx - UI quest gan POI.
  Chuc nang chi tiet:
- Hien thi quest gan POI

## 10) Gamification (XP, badges)

BE:

- API: be/app/api/v1/gamification.py
  - Route xp history, badge.
- Service: be/app/services/gamification/
  - Logic tinh XP, badge.
- Schema: be/app/schemas/gamification.py
  - DTO xp/badge.
- Model: be/app/models/xp_transaction.py, be/app/models/badge.py, be/app/models/auth.py (levels) - xp_transactions, badges, levels.
  Chuc nang chi tiet:
- Cap XP khi quest duyet
- Lich su XP
- Badge va dieu kien trao
  Mobile:
- Service: mobile/services/xpHistoryService.ts - Goi API lich su XP.
  Chuc nang chi tiet:
- Xem lich su XP

## 11) Admin

BE:

- API: be/app/api/v1/admin.py
  - Route admin thao tac.
- Service: be/app/services/admin/
  - Logic quan tri.
- Schema: be/app/schemas/admin.py
  - DTO admin.
- Model: be/app/models/audit.py - audit_logs.
  Chuc nang chi tiet:
- Quan ly user, quest, submission
- Audit log thao tac

## 12) Uploads

BE:

- API: be/app/api/v1/uploads.py
  - Route signed upload.
- Service: be/app/services/upload/
  - Logic upload.
- Schema: be/app/schemas/upload.py - DTO upload.
  Chuc nang chi tiet:
- Signed upload
- Validate loai file
  Mobile:
- Service: mobile/services/uploadService.ts - Goi API upload.
  Chuc nang chi tiet:
- Upload tu mobile

## 13) Email OTP

BE:

- API: be/app/api/v1/auth.py
  - Route otp, reset password.
- Service: be/app/services/email/, be/app/services/otp/
  - Gui email, luu OTP.
- Schema: be/app/schemas/auth.py - DTO otp.
  Chuc nang chi tiet:
- Gui OTP
- Verify OTP
- Rate limit resend

## 14) Infra & cross-cutting

BE:

- App entry: be/app/main.py
  - Khoi tao app, mount middleware.
- Router: be/app/api/v1/router.py
  - Gom tat ca API.
- Middleware: be/app/middleware/
  - Online tracking, logging.
- Workers: be/app/workers/
  - Job nen/async tasks.
- Config: be/app/core/
  - Settings, security, redis.
- Rules/Scoring: be/app/services/rules/, be/app/services/scoring/ - Rule engine, score logic.
  Mobile:
- Http client: mobile/services/httpClient.ts
  - Wrapper fetch, retry, refresh token.
- Contexts: mobile/contexts/ - Global state (auth, user, toast).
  Chuc nang chi tiet:
- Logging, error handling
- Config, env, dependency injection
- Rules/Scoring cho AI va cheat detection
