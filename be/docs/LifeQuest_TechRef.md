+-----------------------------------------------------------------------+
| **LIFEQUEST**                                                         |
|                                                                       |
| Technical Reference Document                                          |
|                                                                       |
| DB Schema · Folder Structure · System Design (BE / FE / Mobile)       |
+-----------------------------------------------------------------------+

+-----------------+-----------------+-----------------+-----------------+
| **Backend**     | **Database**    | **Mobile**      | **Admin**       |
|                 |                 |                 |                 |
| **FastAPI +     | **PostgreSQL +  | **React         | **React Web +   |
| Python**        | Redis**         | Native + Expo** | Vite**          |
+-----------------+-----------------+-----------------+-----------------+

**1. Database Schema**

17 bảng, PostgreSQL. Ảnh lưu trên Cloudinary --- DB chỉ lưu image_url và
cloudinary_public_id. Redis dùng cho cache và rate limit, không lưu
business data.

**1.1 Tổng quan các bảng**

  ---------------------- -------------- -------------------------------------------------
  **Bảng**               **Nhóm**       **Vai trò**

  **users**              Auth           Tài khoản, XP, level, streak_days, trust_score,
                                        role (user\|admin), is_banned,
                                        onboarding_completed

  **levels**             Auth           Bảng tĩnh 10 dòng --- ngưỡng XP từng level. Seed
                                        ngay trong migration

  **refresh_tokens**     Auth           Token đã phát, is_revoked + expires_at để thu hồi
                                        ngay khi logout/đổi role

  **user_preferences**   Onboarding     Sở thích (ARRAY int), interest_weights (JSONB ---
                                        recommendation tự cập nhật), activity_level,
                                        location/notif

  **categories**         Quest          Danh mục quest --- dùng cho onboarding và
                                        recommendation

  **quests**             Quest          Kho quest do admin tạo --- xp_reward, difficulty,
                                        approval_rate, time_limit_hours,
                                        location_required

  **quest_categories**   Quest          Junction M:N giữa quests và categories

  **user_quests**        Quest          Tiến trình mỗi user với mỗi quest.
                                        UNIQUE(user_id, quest_id). Status machine:
                                        in_progress→submitted→approved/rejected/expired

  **submissions**        Submission     Bằng chứng ảnh --- image_url,
                                        cloudinary_public_id, file_hash (anti-cheat),
                                        exif_data, cheat_flags, ai_score. Status:
                                        pending\|approved\|rejected\|manual_review

  **xp_transactions**    Gamification   Audit log bất biến --- chỉ INSERT. submission_id
                                        làm khóa idempotency, source ghi nguồn XP

  **badges**             Gamification   Criteria JSONB linh hoạt: quest_count, streak,
                                        category. Admin CRUD

  **user_badges**        Gamification   UNIQUE(user_id, badge_id) --- không trao trùng.
                                        earned_at để timeline profile

  **follows**            Social         Đồ thị follow. PK(follower_id, following_id).
                                        Feed query dùng bảng này

  **posts**              Social         Tạo tự động khi submission approved. user_id
                                        denorm để feed query nhanh. like_count,
                                        comment_count denorm

  **likes**              Social         PK(user_id, post_id) --- không like trùng. Mỗi
                                        INSERT/DELETE cập nhật posts.like_count

  **comments**           Social         parent_id tự tham chiếu cho reply. is_deleted =
                                        soft delete, không xóa thật

  **notifications**      System         type + data JSONB linh hoạt. Index (user_id,
                                        is_read) để query unread nhanh
  ---------------------- -------------- -------------------------------------------------

**1.2 Chi tiết từng bảng**

**users**

  ---------------------- -------------- ---------------- --------------------------------
  **Column**             **Type**       **Constraint**   **Mô tả**

  id                     UUID           PK               Tự sinh UUID

  username               VARCHAR(50)    UNIQUE NOT NULL  Tên đăng nhập

  email                  VARCHAR(100)   UNIQUE NOT NULL  Email đăng nhập

  password_hash          VARCHAR(255)   NOT NULL         bcrypt hash

  level_id               INTEGER        FK → levels      Level hiện tại, default 1

  xp                     INTEGER        NOT NULL default Tổng XP tích lũy
                                        0                

  streak_days            INTEGER        NOT NULL default Chuỗi ngày liên tiếp
                                        0                

  trust_score            FLOAT          NOT NULL default AI dùng để điều chỉnh ngưỡng
                                        1.0              duyệt

  role                   VARCHAR(20)    NOT NULL default \'user\' hoặc \'admin\'
                                        \'user\'         

  is_banned              BOOLEAN        NOT NULL default Khóa tài khoản
                                        false            

  onboarding_completed   BOOLEAN        NOT NULL default Đã qua màn chọn sở thích chưa
                                        false            

  created_at             TIMESTAMP      server_default   
                                        now()            

  updated_at             TIMESTAMP      server_default   
                                        now()            
  ---------------------- -------------- ---------------- --------------------------------

**submissions**

  ---------------------- -------------- ---------------- --------------------------------------------
  **Column**             **Type**       **Constraint**   **Mô tả**

  id                     UUID           PK               

  user_quest_id          UUID           FK → user_quests 1 quest chỉ có 1 submission
                                        UNIQUE           

  image_url              VARCHAR(500)   NOT NULL         URL Cloudinary để hiển thị ảnh

  cloudinary_public_id   VARCHAR(255)   NOT NULL         ID để xóa ảnh khi reject

  file_hash              VARCHAR(64)    NOT NULL         MD5/SHA256 --- anti-cheat detect ảnh dùng
                                                         lại

  exif_data              JSONB          nullable         Metadata ảnh: timestamp chụp, GPS

  cheat_flags            JSONB          nullable         Kết quả từng rule anti-cheat

  ai_score               FLOAT          nullable         Điểm Google Vision trả về

  status                 VARCHAR(20)    NOT NULL default pending\|approved\|rejected\|manual_review
                                        \'pending\'      

  is_suspicious          BOOLEAN        NOT NULL default Admin filter nhanh
                                        false            

  rejection_reason       TEXT           nullable         Lý do reject (manual)

  created_at             TIMESTAMP      server_default   
                                        now()            
  ---------------------- -------------- ---------------- --------------------------------------------

**Các bảng còn lại --- field quan trọng**

  ------------------ ------------------ ---------------------------------------
  **Bảng**           **Field đặc biệt** **Lý do**

  user_preferences   interests          Mảng category_id. JSONB
                     ARRAY(int)         interest_weights tự cập nhật sau mỗi
                                        quest approve

  quests             xp_reward,         approval_rate tự tính bởi trigger khi
                     difficulty,        submission thay đổi status
                     approval_rate      

  user_quests        expires_at, status expires_at = started_at +
                                        time_limit_hours. Status machine chặt
                                        chẽ

  xp_transactions    amount, source,    submission_id làm idempotency key ---
                     submission_id FK   check trước khi cấp XP

  posts              user_id FK,        user_id denorm tránh join nặng.
                     like_count,        like/comment count denorm cho feed
                     comment_count      query

  refresh_tokens     token_hash,        expires_at để cron dọn. is_revoked để
                     expires_at,        thu hồi ngay không cần chờ hết hạn
                     is_revoked         

  badges             criteria JSONB     Linh hoạt:
                                        {type:\'quest_count\',value:10} hoặc
                                        {type:\'streak\',value:7}
  ------------------ ------------------ ---------------------------------------

**1.3 Indexes**

  ---------------------------------- ----------------- -------------------------------
  **Index**                          **Bảng**          **Dùng cho**

  ix_notifications_user_unread       notifications     Query thông báo chưa đọc của
                                                       user

  ix_submissions_status              submissions       Admin lọc pending/manual_review

  ix_submissions_file_hash           submissions       Anti-cheat detect ảnh dùng lại

  ix_submissions_suspicious          submissions       Admin lọc is_suspicious=true

  ix_user_quests_user_status         user_quests       Lấy quest đang in_progress của
                                                       user

  ix_quests_is_active                quests            Chỉ lấy quest active cho feed

  ix_posts_user_id                   posts             Feed query theo following list

  ix_posts_created_at                posts             Sort feed theo thời gian

  ix_comments_post_id                comments          Lấy comment của một post

  ix_likes_post_id                   likes             Đếm like, check user đã like
                                                       chưa

  ix_follows_following_id            follows           Ai đang follow user này

  ix_xp_transactions_user_id         xp_transactions   Lịch sử XP của user

  ix_xp_transactions_submission_id   xp_transactions   Idempotency check trước khi cấp
                                                       XP

  ix_refresh_tokens_user_id          refresh_tokens    Thu hồi tất cả token của user

  ix_user_badges_user_id             user_badges       Lấy badge của user
  ---------------------------------- ----------------- -------------------------------

Ảnh KHÔNG lưu trong DB. PostgreSQL chỉ lưu image_url và
cloudinary_public_id. Cloudinary lo CDN, nén, optimize format. file_hash
lưu để anti-cheat so sánh --- không phải để lấy lại ảnh.

**2. Folder Structure**

3 repo riêng biệt: backend (FastAPI), mobile app (React Native + Expo),
admin panel (React Web + Vite).

**2.1 Backend --- lifequest-backend/**

  ------------------------------------------------- ------------------------
  **Đường dẫn**                                     **Ghi chú**

  **lifequest-backend/**                            

  **app/**                                          

  main.py                                           Khởi động FastAPI, mount
                                                    middleware

  **api/**                                          

  **v1/**                                           

  router.py                                         Gộp tất cả routers

  auth.py                                           register, login,
                                                    refresh, logout

  users.py                                          profile, preferences

  quests.py                                         list, detail, start,
                                                    submit, history

  submissions.py                                    detail, status

  social.py                                         feed, follow, like,
                                                    comment

  gamification.py                                   badges, xp-history

  recommendations.py                                quest gợi ý cá nhân hóa

  notifications.py                                  list, mark read

  **admin/**                                        

  quests.py                                         CRUD quest + category

  submissions.py                                    queue pending, approve,
                                                    manual review

  users.py                                          list, ban, đổi role

  badges.py                                         CRUD badge, grant thủ
                                                    công

  stats.py                                          dashboard, audit log XP

  **deps/**                                         

  auth.py                                           get_current_user(),
                                                    require_admin()

  db.py                                             get_db() session
                                                    dependency

  **services/**                                     

  auth_service.py                                   register, login, token

  preference_service.py                             lưu sở thích, invalidate
                                                    cache

  quest_service.py                                  start, submit,
                                                    anti-cheat nhanh

  submission_service.py                             approve, reject, pending
                                                    queue

  ai_approval_service.py                            Google Vision API +
                                                    rule-based

  recommendation_service.py                         scoring đa yếu tố +
                                                    cache Redis

  xp_service.py                                     cấp XP idempotent

  badge_service.py                                  kiểm tra criteria JSONB

  upload_service.py                                 Cloudinary + EXIF +
                                                    file_hash

  social_service.py                                 feed, follow, like,
                                                    comment

  notification_service.py                           tạo và đọc notification

  admin_service.py                                  stats, ban user, đổi
                                                    role

  **models/**                                       

  base.py                                           UUIDMixin,
                                                    TimestampMixin

  user.py                                           

  user_preference.py                                

  quest.py                                          quests + categories +
                                                    quest_categories

  user_quest.py                                     

  submission.py                                     

  badge.py                                          badges + user_badges

  xp_transaction.py                                 

  social.py                                         follows + posts +
                                                    likes + comments

  notification.py                                   

  auth.py                                           refresh_tokens + levels

  **schemas/**                                      

  auth.py                                           RegisterRequest,
                                                    LoginRequest,
                                                    TokenResponse

  user.py                                           UserMeResponse,
                                                    UpdateProfileRequest

  preference.py                                     PreferenceRequest,
                                                    PreferenceResponse

  quest.py                                          QuestListResponse,
                                                    StartQuestResponse

  submission.py                                     SubmitProofRequest,
                                                    SubmissionResponse

  social.py                                         FeedItem,
                                                    CommentResponse

  gamification.py                                   BadgeResponse,
                                                    XpHistoryItem

  admin.py                                          AdminUserResponse,
                                                    DashboardStatsResponse

  common.py                                         PaginatedResponse,
                                                    ErrorResponse

  **core/**                                         

  config.py                                         Settings từ .env ---
                                                    fail fast nếu thiếu

  security.py                                       JWT, bcrypt, token
                                                    blacklist Redis

  database.py                                       SQLAlchemy engine +
                                                    session

  redis.py                                          Redis client + helpers

  exceptions.py                                     Custom exceptions

  **middleware/**                                   

  cors.py                                           

  rate_limit.py                                     

  logging.py                                        

  error_handler.py                                  

  **workers/**                                      

  celery_app.py                                     Celery instance + Redis
                                                    broker + beat schedule

  approval_tasks.py                                 AI Vision + rule-based
                                                    deep check

  reward_tasks.py                                   XP + badge + tạo post tự
                                                    động

  notification_tasks.py                             Push notification FCM

  maintenance_tasks.py                              Cron: expire quest, dọn
                                                    token, cache

  **migrations/**                                   

  env.py                                            

  **versions/**                                     Alembic migration files

  **tests/**                                        

  test_auth.py                                      

  test_quest.py                                     

  test_submission.py                                

  test_recommendation.py                            

  .env                                              KHÔNG commit git

  .env.example                                      Template với placeholder

  Dockerfile                                        

  docker-compose.yml                                postgres + redis +
                                                    celery

  requirements.txt                                  

  alembic.ini                                       
  ------------------------------------------------- ------------------------

**2.2 Mobile App --- lifequest-app/**

  ------------------------------------------------- ---------------------
  **Đường dẫn**                                     **Ghi chú**

  **lifequest-app/**                                

  **src/**                                          

  **screens/**                                      

  **auth/**                                         

  LoginScreen.tsx                                   

  RegisterScreen.tsx                                

  **onboarding/**                                   

  InterestPickerScreen.tsx                          Multi-select chip
                                                    (min 3)

  ActivityLevelScreen.tsx                           

  LocationPermissionScreen.tsx                      

  **home/**                                         

  HomeScreen.tsx                                    Quest feed được
                                                    recommend

  QuestDetailScreen.tsx                             

  SubmitProofScreen.tsx                             Camera + compress +
                                                    hash + upload

  **social/**                                       

  FeedScreen.tsx                                    Feed người đang
                                                    follow

  PostDetailScreen.tsx                              Like, comment, reply

  **profile/**                                      

  ProfileScreen.tsx                                 XP bar, level,
                                                    badges, lịch sử

  SettingsScreen.tsx                                Sở thích, notif, đăng
                                                    xuất

  EditProfileScreen.tsx                             

  XpHistoryScreen.tsx                               

  BadgeListScreen.tsx                               

  **notifications/**                                

  NotificationScreen.tsx                            

  **components/**                                   

  QuestCard.tsx                                     

  FeedItem.tsx                                      

  XpBar.tsx                                         

  BadgeChip.tsx                                     

  InterestChip.tsx                                  

  CommentItem.tsx                                   

  SubmissionStatusBadge.tsx                         pending / approved /
                                                    manual_review

  **hooks/**                                        

  useAuth.ts                                        

  useQuest.ts                                       

  useSubmit.ts                                      compress → hash →
                                                    upload → submit

  useFeed.ts                                        Infinite scroll

  useNotifications.ts                               

  usePreferences.ts                                 

  useRecommendation.ts                              

  **store/**                                        

  authStore.ts                                      token, user, role
                                                    (Zustand)

  questStore.ts                                     

  feedStore.ts                                      

  preferenceStore.ts                                

  uiStore.ts                                        Loading states toàn
                                                    app

  **api/**                                          

  client.ts                                         Axios + auto attach
                                                    JWT + auto refresh

  auth.api.ts                                       

  quest.api.ts                                      

  social.api.ts                                     

  user.api.ts                                       

  types.ts                                          Shared TypeScript
                                                    types

  **navigation/**                                   

  RootNavigator.tsx                                 

  AuthNavigator.tsx                                 

  OnboardingNavigator.tsx                           

  MainTabNavigator.tsx                              Home, Feed, Profile,
                                                    Notifications

  guards.tsx                                        AuthGuard +
                                                    OnboardingGuard

  **utils/**                                        

  imageUtils.ts                                     Compress, pick từ
                                                    camera/gallery, EXIF

  hashUtils.ts                                      MD5 file hash cho
                                                    anti-cheat

  formatter.ts                                      XP, level, time
                                                    format

  **\_\_tests\_\_/**                                

  app.json                                          Expo config

  app.config.ts                                     

  babel.config.js                                   

  tsconfig.json                                     

  package.json                                      

  .env                                              API_URL, Cloudinary
                                                    key
  ------------------------------------------------- ---------------------

**2.3 Admin Panel --- lifequest-admin/**

  ------------------------------------------------- ---------------------
  **Đường dẫn**                                     **Ghi chú**

  **lifequest-admin/**                              

  **src/**                                          

  **pages/**                                        

  LoginPage.tsx                                     Chỉ admin đăng nhập

  DashboardPage.tsx                                 Stats tổng quan

  SubmissionsPage.tsx                               Hàng đợi pending +
                                                    manual_review

  SubmissionDetailPage.tsx                          Ảnh, EXIF,
                                                    cheat_flags, approve

  QuestsPage.tsx                                    Danh sách quest

  QuestFormPage.tsx                                 Tạo / sửa quest

  UsersPage.tsx                                     Danh sách user

  UserDetailPage.tsx                                Lịch sử, ban/unban,
                                                    đổi role

  BadgesPage.tsx                                    CRUD badge

  CategoriesPage.tsx                                CRUD category

  XpAuditPage.tsx                                   Audit log XP toàn bộ

  **components/**                                   

  Sidebar.tsx                                       

  DataTable.tsx                                     Reusable table +
                                                    pagination

  SubmissionViewer.tsx                              Ảnh + metadata + nút
                                                    approve

  StatCard.tsx                                      

  StatusBadge.tsx                                   

  ConfirmDialog.tsx                                 Confirm trước khi
                                                    ban/approve

  **api/**                                          

  client.ts                                         Axios + admin token

  submissions.api.ts                                

  quests.api.ts                                     

  users.api.ts                                      

  badges.api.ts                                     

  stats.api.ts                                      

  **hooks/**                                        

  useAdminAuth.ts                                   Kiểm tra role=admin

  useSubmissions.ts                                 

  useUsers.ts                                       

  useStats.ts                                       

  **guards/**                                       

  AdminRoute.tsx                                    Redirect /403 nếu
                                                    không phải admin

  **store/**                                        

  adminAuthStore.ts                                 

  router.tsx                                        React Router, bọc
                                                    AdminRoute

  App.tsx                                           

  index.html                                        

  vite.config.ts                                    

  tsconfig.json                                     

  package.json                                      

  .env                                              VITE_API_URL
  ------------------------------------------------- ---------------------

**3. System Design --- Backend**

Monolith phân lớp. Luồng 1 chiều duy nhất: Client → API Gateway → Router
→ Service → Model → DB. Không layer nào gọi ngược lên layer trên.

**3.1 API Gateway & Middleware**

  --------------------- -------------------------------------------------
  **Module / File**     **Chức năng**

  **JWT middleware**    Decode Bearer token mỗi request. Inject
                        current_user (id, role) vào context. Trả 401 nếu
                        không hợp lệ. Bỏ qua POST /auth/register và
                        /auth/login.

  **require_admin()**   Dependency kiểm tra role==\'admin\'. Trả 403 nếu
                        không phải admin. Bọc toàn bộ /admin/\* routers.

  **Rate limit          Redis đếm request theo IP. Giới hạn riêng
  middleware**          /auth/login (5 lần/phút). Giới hạn upload ảnh
                        theo user_id.

  **CORS middleware**   Cho phép domain React Native app và
                        admin.lifequest.app.

  **Error handler**     Bắt toàn bộ exception, trả JSON chuẩn hóa. Ẩn
                        stack trace ở production.

  **Request logging**   Log method, path, status, latency, user_id,
                        request_id để trace.
  --------------------- -------------------------------------------------

**3.2 Routers --- /api/v1/**

  -------------------- ---------------------------------- -------------------------------------
  **Router**           **Endpoints chính**                **Ghi chú**

  auth.py              POST /register, /login, /refresh,  Trả onboarding_completed trong login
                       /logout                            response

  users.py             GET/PATCH /users/me,               Preferences dùng cho recommendation
                       GET/POST/PATCH                     
                       /users/me/preferences              

  quests.py            GET /quests, GET /quests/{id},     Submit gọi anti-cheat sync rồi queue
                       POST /quests/{id}/start, POST      Celery task
                       /quests/{id}/submit                

  submissions.py       GET /submissions/{id}              User chỉ xem submission của mình

  recommendations.py   GET /recommendations/quests        Cache Redis 10 phút. Invalidate khi
                                                          preferences thay đổi

  social.py            GET /social/feed, POST             Feed yêu cầu đăng nhập
                       /social/follow/{id}, POST          
                       /social/like/{id}, POST/DELETE     
                       /social/comment                    

  gamification.py      GET /gamification/badges,          
                       /badges/me, /xp-history            

  notifications.py     GET /notifications, PATCH          
                       /notifications/read-all            

  admin/submissions    GET /admin/submissions/pending,    Chỉ admin
                       PATCH                              
                       /admin/submissions/{id}/approve,   
                       PATCH /{id}/manual-review          

  admin/quests         CRUD /admin/quests,                Chỉ admin
                       /admin/categories                  

  admin/users          GET /admin/users, PATCH /{id}/ban, Chỉ admin
                       PATCH /{id}/role                   

  admin/badges         CRUD /admin/badges, POST           Chỉ admin
                       /{id}/grant/{user_id}              

  admin/stats          GET /admin/stats/dashboard,        Chỉ admin
                       /xp-audit                          
  -------------------- ---------------------------------- -------------------------------------

**3.3 Services --- Business Logic**

  ------------------------------- ---------------------------------------------------
  **Module / File**               **Chức năng**

  **auth_service.py**             Register (hash bcrypt, tạo user + user_preferences
                                  rỗng), login (verify, phát JWT với role), refresh,
                                  logout (revoke token Redis + DB).

  **preference_service.py**       Lưu interests + activity_level sau onboarding. Set
                                  onboarding_completed=true. Invalidate
                                  recommendation cache Redis.

  **quest_service.py**            List quests (gọi recommendation_service). Start
                                  quest (tạo user_quest, chặn duplicate). Submit
                                  (anti-cheat sync → upload → lưu submission → queue
                                  approval_task).

  **ai_approval_service.py**      Gọi Google Vision API. Rule-based deep check (GPS
                                  match, screenshot detect). Tính approval score.
                                  Quyết định approved vs manual_review. KHÔNG bao giờ
                                  auto-reject. Cập nhật trust_score.

  **recommendation_service.py**   Tính score 6 yếu tố (interests 35%, difficulty 20%,
                                  location 15%, trending 15%, approval_rate 10%,
                                  novelty 5%). Cache Redis 10 phút. Feedback loop cập
                                  nhật interest_weights sau mỗi approve.

  **xp_service.py**               Check XpTransaction theo submission_id trước khi
                                  cấp (idempotency). Cộng XP, tính lại level_id, ghi
                                  audit log. KHÔNG bao giờ cấp 2 lần.

  **badge_service.py**            Chạy sau mỗi approve. Đọc criteria JSONB của từng
                                  badge. Trao nếu đủ điều kiện. UNIQUE constraint
                                  chặn trùng ở DB layer.

  **upload_service.py**           Validate format + size. Tính file_hash (MD5).
                                  Extract EXIF. Upload Cloudinary. Trả image_url +
                                  cloudinary_public_id.

  **social_service.py**           Feed query posts của following list.
                                  Follow/unfollow. Toggle like (cập nhật like_count).
                                  Comment CRUD (soft delete).

  **admin_service.py**            Dashboard stats. Ban/unban user. Đổi role
                                  (blacklist token cũ Redis). Export XP audit. Thống
                                  kê submission.
  ------------------------------- ---------------------------------------------------

**3.4 Luồng Submit Proof**

  -------- ------------------ ------------------------------------------------
  **\#**   **Bước**           **Chi tiết**

  **1**    **Client nén +     Nén ảnh, tính MD5 hash trước khi upload
           hash**             

  **2**    **Anti-cheat đồng  Kiểm tra file_hash trùng trong DB. Validate EXIF
           bộ**               timestamp trong khoảng thời gian quest active.
                              Validate format/size.

  **3**    **Upload           Nếu pass anti-cheat → upload lên Cloudinary →
           Cloudinary**       nhận image_url + public_id

  **4**    **Lưu + trả        Tạo submission status=\'pending\'. Cập nhật
           response ngay**    user_quest status=\'submitted\'. Trả 200 ngay
                              --- user không chờ AI.

  **5**    **Queue Celery     approval_tasks.py nhận submission_id
           task**             

  **6**    **AI deep check    Google Vision API phân tích nội dung ảnh.
           (background)**     Rule-based: GPS, screenshot detect. Tính score
                              dựa trust_score.

  **7**    **Quyết định**     Score ≥ threshold → approved. Score \< threshold
                              → manual_review. KHÔNG bao giờ auto-reject.

  **8**    **Nếu approved**   reward_tasks.py: cấp XP (idempotent) → tính
                              level → check badge → tạo post → gửi
                              notification. Cập nhật interest_weights.
  -------- ------------------ ------------------------------------------------

**3.5 Workers --- Celery**

  --------------------------- -------------------------------------------------
  **Module / File**           **Chức năng**

  **celery_app.py**           Redis broker (DB 1) + result backend (DB 2).
                              task_acks_late=True --- không mất task khi worker
                              crash. Beat schedule cho cron.

  **approval_tasks.py**       AI auto-approval. Retry tối đa 3 lần. Idempotent
                              --- gọi nhiều lần cho kết quả như nhau.

  **reward_tasks.py**         Cấp XP (check idempotency) → level → badge → tạo
                              post → notification. Retry an toàn.

  **notification_tasks.py**   Push FCM. Bulk notify. Alert quest sắp hết hạn.

  **maintenance_tasks.py**    Mỗi giờ: đánh expired user_quests. Mỗi 5 phút:
                              rebuild leaderboard cache. Mỗi ngày: dọn
                              refresh_tokens hết hạn. Mỗi tuần: recalculate
                              interest_weights.
  --------------------------- -------------------------------------------------

**3.6 Quy tắc kiến trúc cứng**

  -------- ------------------------------------------------------------------
  **\#**   **Quy tắc**

  **1**    Luồng 1 chiều: Router → Service → Model → DB. Không gọi ngược.

  **2**    Router không tự query DB --- chỉ gọi service.

  **3**    Service không gọi router. Service không gọi service khác theo vòng
           tròn.

  **4**    XP chỉ cấp qua xp_service --- đảm bảo idempotency.

  **5**    Mọi thay đổi XP phải có XpTransaction record --- audit bất biến.

  **6**    KHÔNG bao giờ auto-reject submission --- chỉ approved hoặc
           manual_review.

  **7**    Admin endpoints phải có require_admin() dependency --- không chỉ
           kiểm tra ở FE.

  **8**    UNIQUE constraint phòng duplicate ở tầng DB, không chỉ
           application.

  **9**    Role thay đổi → blacklist token cũ Redis để có hiệu lực ngay.

  **10**   Celery task phải idempotent --- retry an toàn không gây side
           effect kép.

  **11**   onboarding_completed=false → chặn truy cập quest endpoints.

  **12**   Không commit .env vào git --- dùng .env.example làm template.
  -------- ------------------------------------------------------------------

**4. System Design --- Mobile App (React Native + Expo)**

**4.1 Navigation & Guards**

  ------------------------- ----------------------------------------------------
  **Navigator / Guard**     **Logic**

  **RootNavigator**         Entry point. Đọc authStore → nếu chưa login →
                            AuthNavigator. Nếu đã login và
                            onboarding_completed=false → OnboardingNavigator.
                            Nếu đã login và hoàn tất onboarding →
                            MainTabNavigator.

  **AuthNavigator**         Stack: Login ↔ Register.

  **OnboardingNavigator**   Stack wizard: InterestPicker → ActivityLevel →
                            LocationPermission. Khi hoàn tất gọi POST
                            /users/me/preferences → set
                            onboarding_completed=true → navigate về
                            MainTabNavigator.

  **MainTabNavigator**      4 tabs: Home (quest feed), Feed (social), Profile,
                            Notifications.

  **AuthGuard**             HOC bọc MainTabNavigator. Nếu token hết hạn và
                            refresh thất bại → logout → về Login.

  **OnboardingGuard**       Nếu user đã login nhưng onboarding_completed=false →
                            redirect OnboardingNavigator dù navigate đến đâu.
  ------------------------- ----------------------------------------------------

**4.2 State Management --- Zustand**

  --------------------- -------------------------------------------------
  **Module / File**     **Chức năng**

  **authStore**         token (access + refresh), user (id, username,
                        role, onboarding_completed), isLoggedIn. Action:
                        login, logout, refreshToken.

  **questStore**        Danh sách quest recommended, quest đang active
                        (in_progress), lịch sử. Action: fetchRecommended,
                        startQuest, submitProof.

  **feedStore**         Danh sách posts, pagination cursor, loading
                        state. Action: fetchFeed, loadMore, toggleLike,
                        addComment.

  **preferenceStore**   interests, activity_level, location_enabled.
                        Action: savePreferences, updateInterests.

  **uiStore**           Global loading, toast messages, modal states.
  --------------------- -------------------------------------------------

**4.3 API Client --- Axios**

  --------------------- -------------------------------------------------
  **Module / File**     **Chức năng**

  **Auto attach JWT**   Request interceptor gắn Authorization: Bearer
                        {token} vào mọi request.

  **Auto refresh        Response interceptor bắt lỗi 401 → gọi POST
  token**               /auth/refresh → retry request gốc → nếu refresh
                        thất bại → logout.

  **Retry khi mất       Exponential backoff, retry tối đa 3 lần cho lỗi
  mạng**                network.

  **Upload multipart**  useSubmit hook compress ảnh → tính MD5 hash →
                        upload Cloudinary trực tiếp từ client → gửi
                        image_url + file_hash lên backend.

  **Handle 403**        Redirect về màn hình phù hợp nếu user bị ban hoặc
                        token không hợp lệ.
  --------------------- -------------------------------------------------

**4.4 Luồng Submit Proof trên Mobile**

  -------- ---------------- -------------------------------------------------
  **\#**   **Bước**         **Chi tiết**

  **1**    **Chọn ảnh**     Camera hoặc gallery picker (expo-image-picker).
                            Kiểm tra permission.

  **2**    **Nén ảnh**      expo-image-manipulator giảm kích thước xuống tối
                            đa 1200px, quality 0.85.

  **3**    **Tính hash**    MD5 của file sau khi nén (hashUtils.ts). Gửi kèm
                            để backend anti-cheat.

  **4**    **Upload         Multipart POST trực tiếp lên Cloudinary. Nhận
           Cloudinary**     image_url + public_id.

  **5**    **Submit lên     POST /quests/{id}/submit với image_url,
           backend**        cloudinary_public_id, file_hash.

  **6**    **Nhận response  Backend trả 200 ngay với status=\'pending\'. Hiển
           ngay**           thị \'Đang xem xét\'.

  **7**    **Nhận           Push notification hoặc in-app khi AI quyết định
           notification**   approved/manual_review.
  -------- ---------------- -------------------------------------------------

**4.5 Screens & Trách nhiệm**

  -------------------------- -------------------------------------------------
  **Module / File**          **Chức năng**

  **LoginScreen /            Form đăng nhập/đăng ký. Sau đăng nhập check
  RegisterScreen**           onboarding_completed để navigate đúng luồng.

  **InterestPickerScreen**   Multi-select chips từ danh sách categories.
                             Validate min 3 trước khi tiếp tục.

  **HomeScreen**             Gọi GET /recommendations/quests. Hiển thị danh
                             sách QuestCard. Pull-to-refresh invalidate cache.

  **QuestDetailScreen**      Chi tiết quest, timer đếm ngược, nút Start +
                             Submit.

  **SubmitProofScreen**      Camera/gallery picker, preview ảnh, nút submit.
                             Hiển thị loading trong khi upload.

  **FeedScreen**             Infinite scroll posts của following. FeedItem
                             hiển thị ảnh quest + like + comment count.

  **PostDetailScreen**       Chi tiết post, danh sách comments (hỗ trợ reply),
                             input thêm comment.

  **ProfileScreen**          XpBar animation, LevelBadge, danh sách BadgeChip,
                             lịch sử quest theo status.

  **SettingsScreen**         Cập nhật interests (gọi PATCH
                             /users/me/preferences), toggle
                             location/notification, đăng xuất.

  **NotificationScreen**     Danh sách notifications, mark read khi scroll
                             qua.
  -------------------------- -------------------------------------------------

**5. System Design --- Admin Panel (React Web + Vite)**

Ứng dụng web riêng biệt. Toàn bộ route bọc trong AdminRoute guard. Chỉ
truy cập được khi đăng nhập bằng tài khoản role=admin.

**5.1 Tính năng Admin**

  ---------------- ------------------------------------------------------
  **Trang**        **Chức năng chi tiết**

  **Dashboard**    Số user active, quest hoàn thành hôm nay, submission
                   pending, approval rate tổng, XP được cấp hôm nay, top
                   categories theo completion.

  **Submissions    Bảng hàng đợi pending + manual_review. Filter theo
  Queue**          status, is_suspicious. Sort theo thời gian.

  **Submission     Xem ảnh proof full size. EXIF metadata (thời gian
  Detail**         chụp, GPS). cheat_flags chi tiết. ai_score. Lịch sử
                   submission của user đó. Nút Approve / Manual Review
                   (không có Reject ngay).

  **Quests**       Danh sách tất cả quest. Filter active/inactive. Nút
                   tạo mới, sửa, ẩn quest.

  **Quest Form**   Tạo/sửa quest: title, description, xp_reward,
                   difficulty, time_limit_hours, location_required, chọn
                   categories.

  **Users**        Danh sách user. Search theo username/email. Filter
                   is_banned. Xem trust_score.

  **User Detail**  Profile đầy đủ, lịch sử quest, lịch sử XP, badges. Nút
                   ban/unban. Nút đổi role user↔admin.

  **Badges**       Danh sách badge. Form tạo/sửa với criteria JSONB
                   editor. Nút grant thủ công cho user cụ thể.

  **Categories**   CRUD category. Xem số quest theo từng category.

  **XP Audit Log** Toàn bộ xp_transactions. Filter theo user, source,
                   thời gian. Xem submission_id liên kết.
  ---------------- ------------------------------------------------------

**5.2 Phân quyền Admin vs User**

  ----------------------------------- ----------------- -----------------
  **Tính năng**                       **USER**          **ADMIN**

  Đăng nhập / Đăng ký                 ✅                ✅

  Onboarding + chọn sở thích          ✅                ✅

  Xem & làm quest                     ✅                ✅

  Submit proof ảnh                    ✅                ✅

  Nhận XP, badge, level               ✅                ✅

  Feed + like + comment + follow      ✅                ✅

  Cập nhật profile cá nhân            ✅                ✅

  Xem hàng đợi pending submissions    ❌                ✅

  Approve / Manual review submission  ❌                ✅

  Xem EXIF, cheat_flags, ai_score     ❌                ✅

  Tạo / sửa / ẩn quest                ❌                ✅

  Quản lý user (ban, đổi role)        ❌                ✅

  CRUD badge, category                ❌                ✅

  Xem XP audit log                    ❌                ✅

  Xem dashboard thống kê              ❌                ✅
  ----------------------------------- ----------------- -----------------

LifeQuest Technical Reference v1.0 · 04/2026 · FastAPI + PostgreSQL +
React Native + Expo + React Web
