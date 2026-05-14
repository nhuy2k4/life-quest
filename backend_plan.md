# KẾ HOẠCH PHÁT TRIỂN BACKEND HỆ THỐNG

## 1. Auth (Đã hoàn thành)

**Branch:** feature/auth

### API

-   POST /auth/register -- Đăng ký
-   POST /auth/login -- Đăng nhập
-   POST /auth/google/login -- Đăng nhập Google
-   POST /auth/verify-email -- Xác thực email
-   POST /auth/resend-otp -- Gửi lại OTP
-   POST /auth/logout -- Đăng xuất

### Database

-   users (email, password_hash, is_active, ...)
-   refresh_tokens

### Services

-   auth_service.py
-   jwt_service.py

### Ghi chú

-   Đã hoàn thành luồng auth cơ bản
-   Sẵn sàng merge vào main

------------------------------------------------------------------------

## 2. User + Preferences (Onboarding)

**Branch:** feature/user-onboarding

### API

-   GET /users/me → Lấy thông tin user
-   PATCH /users/me → Cập nhật profile
-   POST /users/me/preferences → Lưu sở thích
-   GET /users/me/preferences → Lấy sở thích

### Database

-   users → thêm onboarding_completed
-   user_preferences (interests, activity_level)

### Logic

-   Sau login → kiểm tra onboarding_completed
-   Nếu false → bắt buộc onboarding
-   Hoàn thành → set true

### Unlock

-   Quest System
-   Recommendation

------------------------------------------------------------------------

## 3. Quest System

**Branch:** feature/quest-system

### API

-   GET /quests
-   GET /quests/{id}
-   POST /quests/{id}/start
-   POST /quests/{id}/submit

### Database

-   quests
-   user_quests

### Logic

-   start → tạo user_quest
-   submit → update status

------------------------------------------------------------------------

## 4. Submission (Upload)

**Branch:** feature/submission

### API

-   POST /quests/{id}/submit
-   GET /submissions/{id}

### Database

-   submissions (image_url, file_hash, status)

### Logic

-   Upload file
-   Hash chống duplicate
-   Link user_quests

------------------------------------------------------------------------

## 5. XP + Level

**Branch:** feature/xp-level

### API

-   GET /gamification/xp-history

### Database

-   user_xp

### Logic

-   Approved → +XP
-   Tính level
-   Idempotent

------------------------------------------------------------------------

## 6. Recommendation

**Branch:** feature/recommendation

### API

-   GET /recommendations/quests

### Logic

-   Dựa vào preferences + history

------------------------------------------------------------------------

## 7. Social

**Branch:** feature/social

### API

-   Feed, Like, Comment, Follow

### Database

-   posts, likes, comments, follows

------------------------------------------------------------------------

## 8. Admin Panel

**Branch:** feature/admin-panel

### Chức năng

-   Manage users, quests, submissions, XP, social

------------------------------------------------------------------------

## 🔄 Thứ tự Merge Git

feature/auth\
→ feature/user-onboarding\
→ feature/quest-system\
→ feature/submission\
→ feature/xp-level\
→ feature/recommendation\
→ feature/social\
→ feature/admin-panel

------------------------------------------------------------------------

## 🧠 Best Practices

-   Luôn sync main\
-   Dùng feature toggle\
-   Mỗi branch có test + seed data\
-   Naming: feature/`<scope>`{=html}\
-   Không gộp nhiều feature
