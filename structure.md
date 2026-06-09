# Database Structure (LifeQuest)

Ghi chu: Noi dung duoc tong hop tu SQLAlchemy models trong be/app/models va cac migration. Moi bang gom chuc nang va danh sach truong chinh.

## 1) Auth & User

### levels

Chuc nang: Bang tinh (seed). Dinh nghia nguong XP cho tung level.

- id (int, PK): ID level.
- name (string): Ten level.
- required_xp (int): Tong XP can de dat level.

### users

Chuc nang: Tai khoan nguoi dung, thong tin ho so, quyen, gamification.

- id (uuid, PK): Khoa chinh.
- username (string, unique): Ten dang nhap.
- display_name (string, nullable): Ten hien thi.
- bio (string, nullable): Mo ta ngan.
- email (string, unique): Email dang nhap.
- password_hash (string, nullable): Hash mat khau (local).
- provider (enum: local/google): Nguon dang nhap.
- provider_id (string, nullable): ID tu nha cung cap.
- level_id (int, FK levels): Level hien tai.
- xp (int): Tong XP tich luy.
- streak_days (int): So ngay giu streak.
- trust_score (float): Diem tin cay cho duyet AI.
- role (enum: user/admin): Quyen truy cap.
- is_verified (bool): Da xac minh email chua.
- is_banned (bool): Khoa tai khoan.
- onboarding_completed (bool): Da hoan tat onboarding.
- created_at (datetime): Thoi diem tao.
- updated_at (datetime): Thoi diem cap nhat.

### refresh_tokens

Chuc nang: Luu refresh token (dang hash) de xoay vong va thu hoi.

- id (uuid, PK): Khoa chinh.
- user_id (uuid, FK users): Chu so huu token.
- token_hash (string, unique): SHA256 cua refresh token.
- is_revoked (bool): Da thu hoi hay chua.
- expires_at (datetime): Het han.
- created_at (datetime): Thoi diem tao.

### user_preferences

Chuc nang: So thich va cau hinh nguoi dung cho onboarding + recommendation.

- id (uuid, PK): Khoa chinh.
- user_id (uuid, FK users, unique): Moi user mot dong.
- interests (json): Danh sach category_id da chon.
- interest_weights (json): Trong so so thich theo category.
- activity_level (enum: low/medium/high, nullable): Muc do hoat dong.
- location_enabled (bool): Cho phep dung vi tri.
- notification_enabled (bool): Cho phep thong bao.

## 2) Quest

### categories

Chuc nang: Danh muc quest.

- id (int, PK): ID danh muc.
- slug (string, unique, nullable): Ten rut gon (slug).
- name (string, unique): Ten danh muc.
- icon (string, nullable): Icon.

### quests

Chuc nang: Kho quest do admin tao.

- id (uuid, PK): Khoa chinh.
- title (string): Tieu de quest.
- description (text, nullable): Mo ta.
- vision_spec (json, nullable): Cau hinh AI/vision.
- template (string, nullable): Template prompt/format.
- labels (json, nullable): Danh sach label mong doi.
- label_rules (json, nullable): Rule danh gia label.
- min_confidence (float, nullable): Nguong tin cay AI.
- xp_reward (int): XP thuong.
- difficulty (enum: easy/medium/hard): Do kho.
- approval_rate (float): Ty le duyet.
- time_limit_hours (int, nullable): Gioi han thoi gian.
- location_required (bool): Can vi tri.
- poi_required (bool): Can POI.
- is_active (bool): Quest hoat dong.
- poi_id (uuid, FK pois, nullable): Gan POI.
- created_at (datetime): Thoi diem tao.
- updated_at (datetime): Thoi diem cap nhat.

### quest_categories

Chuc nang: Bang noi nhieu-nhieu giua quests va categories.

- quest_id (uuid, FK quests, PK): Quest.
- category_id (int, FK categories, PK): Category.

### quest_instances

Chuc nang: Instance quest theo user + POI (khong tao quest moi).

- quest_id (uuid, FK quests, PK): Quest goc.
- user_id (uuid, FK users, PK): User tao instance.
- poi_id (uuid, FK pois, PK): POI duoc gan.
- created_at (datetime): Thoi diem tao.

### user_quests

Chuc nang: Tien trinh quest cua moi user.

- id (uuid, PK): Khoa chinh.
- user_id (uuid, FK users): User.
- quest_id (uuid, FK quests): Quest.
- status (enum): Trang thai (started/submitted/approved/rejected...).
- started_at (datetime, nullable): Thoi diem bat dau.
- expires_at (datetime, nullable): Thoi diem het han.
- consolation_xp (int): XP an ui neu that bai.

### submissions

Chuc nang: Bang chung anh khi nop quest.

- id (uuid, PK): Khoa chinh.
- user_quest_id (uuid, FK user_quests, unique): 1 quest 1 submission.
- image_url (string): URL anh.
- cloudinary_public_id (string): ID tren Cloudinary.
- file_hash (string): Hash de anti-cheat.
- retry_count (int): So lan nop lai.
- vision_labels (json, nullable): Label tu AI.
- vision_raw (json, nullable): Raw response AI.
- ai_metadata (json, nullable): Metadata AI.
- lat (float, nullable): Vi do.
- lng (float, nullable): Kinh do.
- location_accuracy_m (float, nullable): Do chinh xac.
- location_captured_at (datetime, nullable): Thoi diem chup.
- poi_id (uuid, FK pois, nullable): Gan POI.
- poi_distance_m (float, nullable): Khoang cach toi POI.
- cheat_flags (json, nullable): Co cheat.
- ai_score (float, nullable): Diem AI.
- status (enum): pending/processing/approved/rejected/manual_review.
- is_suspicious (bool): Danh dau nghi ngo.
- rejection_reason (text, nullable): Ly do tu choi.
- created_at (datetime): Thoi diem tao.

### ai_detection_logs

Chuc nang: Log chi tiet ket qua AI cho submission.

- id (uuid, PK): Khoa chinh.
- submission_id (uuid, FK submissions): Submission.
- model_version (string, nullable): Version model.
- labels (json, nullable): Label AI.
- ocr_text (text, nullable): OCR text.
- confidence_stats (json, nullable): Thong ke do tin cay.
- raw_response (json, nullable): Raw AI response.
- created_at (datetime): Thoi diem tao.

## 3) Social

### follows

Chuc nang: Quan he follow.

- follower_id (uuid, FK users, PK): Nguoi theo doi.
- following_id (uuid, FK users, PK): Nguoi duoc theo doi.
- created_at (datetime): Thoi diem tao.

### posts

Chuc nang: Bai dang (tu submission approved hoac tao rieng).

- id (uuid, PK): Khoa chinh.
- submission_id (uuid, FK submissions, nullable, unique): Lien ket submission.
- quest_id (uuid, FK quests, nullable): Quest lien quan.
- user_id (uuid, FK users): Tac gia.
- like_count (int): Dem like.
- comment_count (int): Dem comment.
- image_url (text, nullable): Anh bai dang.
- caption (text, nullable): Chu thich.
- location_name (text, nullable): Ten dia diem hien thi.
- created_at (datetime): Thoi diem tao.

### likes

Chuc nang: Like bai dang.

- user_id (uuid, FK users, PK): User.
- post_id (uuid, FK posts, PK): Post.
- created_at (datetime): Thoi diem tao.

### comments

Chuc nang: Binh luan bai dang (ho tro reply).

- id (uuid, PK): Khoa chinh.
- post_id (uuid, FK posts): Post.
- user_id (uuid, FK users): Tac gia.
- parent_id (uuid, FK comments, nullable): Reply.
- content (text): Noi dung.
- is_deleted (bool): Soft delete.
- created_at (datetime): Thoi diem tao.

## 4) Gamification

### xp_transactions

Chuc nang: Lich su cong tru XP (audit, chi insert).

- id (uuid, PK): Khoa chinh.
- user_id (uuid, FK users): User.
- submission_id (uuid, FK submissions, nullable): Dinh danh idempotency.
- amount (int): So XP thay doi.
- source (enum: quest_approved/consolation/admin_adjust): Nguon XP.
- created_at (datetime): Thoi diem tao.

### badges

Chuc nang: Danh hieu.

- id (uuid, PK): Khoa chinh.
- name (string, unique): Ten badge.
- description (text): Mo ta badge.
- icon_url (string): Icon URL hoac icon key.
- rarity (string): Do hiem (common/rare/epic/legendary).
- category (string): Nhom badge.
- criteria (json): Dieu kien trao badge.
- is_hidden (bool): An khoi UI neu chua dat.
- is_active (bool): Badge dang hoat dong.
- sort_order (int): Thu tu hien thi.
- created_at (datetime): Thoi diem tao.
- updated_at (datetime): Thoi diem cap nhat.

### user_badges

Chuc nang: Badge da trao cho user.

- id (uuid, PK): Khoa chinh.
- user_id (uuid, FK users): User.
- badge_id (uuid, FK badges): Badge.
- earned_at (datetime): Thoi diem nhan.

## 5) Notifications

### notifications

Chuc nang: Thong bao he thong.

- id (uuid, PK): Khoa chinh.
- user_id (uuid, FK users): Nguoi nhan.
- type (string): Loai thong bao.
- data (json, nullable): Payload.
- is_read (bool): Da doc hay chua.
- created_at (datetime): Thoi diem tao.

### user_push_tokens

Chuc nang: Luu token push (Expo/FCM).

- id (uuid, PK): Khoa chinh.
- user_id (uuid, FK users): Chu so huu.
- token (string, unique): Token push.
- provider (string): Nha cung cap (expo, fcm...).
- platform (string, nullable): ios/android.
- is_active (bool): Trang thai hoat dong.
- created_at (datetime): Thoi diem tao.
- last_seen_at (datetime): Cap nhat lan cuoi.

## 6) POI

### pois

Chuc nang: Dia diem (Point of Interest) de gan quest.

- id (uuid, PK): Khoa chinh.
- name (string): Ten POI.
- poi_type (string): Loai POI.
- latitude (float): Vi do.
- longitude (float): Kinh do.
- radius_m (float): Ban kinh chap nhan.
- source (string): Nguon du lieu.
- external_id (string): ID ngoai.
- external_type (string, nullable): Loai ngoai.
- is_active (bool): Trang thai hoat dong.
- created_at (datetime): Thoi diem tao.
- updated_at (datetime): Thoi diem cap nhat.

## 7) Recommendation

### recommendation_logs

Chuc nang: Log hanh vi goi recommendation (serving + feedback).

- id (uuid, PK): Khoa chinh.
- user_id (uuid, FK users): User.
- quest_id (uuid, FK quests): Quest.
- event (string): Su kien (impression/click/start...).
- section (string, nullable): Khu vuc hien thi.
- score (float, nullable): Diem he thong.
- rank (int, nullable): Thu tu.
- request_id (uuid): Ma request.
- algorithm_version (string): Version thuat toan.
- reasons (json, nullable): Ly do goi y.
- score_breakdown (json, nullable): Phan ra diem.
- features_snapshot (json, nullable): Snapshot feature.
- rule_score (float, nullable): Diem rule.
- ml_score (float, nullable): Diem ML.
- final_score (float, nullable): Diem tong.
- created_at (datetime): Thoi diem tao.

## 8) Audit

### audit_logs

Chuc nang: Luu vet thao tac quan tri/quan trong.

- id (uuid, PK): Khoa chinh.
- actor_id (uuid, FK users, nullable): Nguoi thuc hien.
- action (string): Hanh dong.
- target_type (string, nullable): Doi tuong tac dong.
- target_id (uuid, nullable): ID doi tuong.
- meta (json, nullable): Payload bo sung.
- created_at (datetime): Thoi diem tao.
