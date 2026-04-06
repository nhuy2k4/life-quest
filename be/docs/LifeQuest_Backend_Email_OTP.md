# LifeQuest Backend: Email OTP & Password Reset Implementation (2026-04-06)

## 1. Email OTP Verification (Đăng ký & xác thực email)

- Khi đăng ký tài khoản local:
  - User được tạo với `is_verified = False`.
  - Sinh OTP 6 số, lưu vào Redis với key `otp:verify_email:{email}` (TTL 5 phút).
  - Gửi OTP qua email (SMTP, cấu hình trong .env).
- API xác thực email: `POST /auth/verify-email` (email + otp)
  - Kiểm tra OTP trong Redis, nếu đúng thì cập nhật `is_verified = True`.
- API gửi lại OTP: `POST /auth/resend-otp` (email)
  - Sinh OTP mới, lưu đè, gửi lại email, có cooldown 60s qua Redis.
- Chặn login nếu user chưa xác thực email.

## 2. Đổi mật khẩu (Change password)

- API: `POST /auth/change-password`
  - Yêu cầu access token (JWT, user đã đăng nhập).
  - Body: `{ "current_password": ..., "new_password": ... }`
  - Kiểm tra mật khẩu cũ, cập nhật mật khẩu mới (chỉ cho user local).

## 3. Quên mật khẩu & Đặt lại mật khẩu (Forgot/Reset password)

- API gửi OTP reset: `POST /auth/forgot-password` (email)
  - Nếu là user local, sinh OTP 6 số, lưu Redis với key `otp:reset_password:{email}` (TTL 5 phút).
  - Gửi OTP qua email, cooldown 60s qua Redis.
- API đặt lại mật khẩu: `POST /auth/reset-password` (email + otp + new_password)
  - Kiểm tra OTP, nếu đúng thì cập nhật mật khẩu mới.

## 4. Cấu trúc code

- `services/otp/otp_service.py`: Sinh, lưu, xác thực OTP cho verify email & reset password (hash OTP, cooldown Redis).
- `services/email/email_service.py`: Gửi email OTP xác thực & reset password qua SMTP.
- `services/auth/auth_service.py`: Business logic cho đăng ký, login, đổi mật khẩu, quên/reset mật khẩu, xác thực email.
- `api/v1/auth.py`: Định nghĩa các endpoint auth, inject service qua Depends.
- `schemas/auth.py`: Định nghĩa các request/response schema cho các flow trên.
- `.env`: Thêm cấu hình SMTP (HOST, PORT, USER, PASSWORD, FROM_EMAIL, USE_TLS).

## 5. Database & Migration

- Thêm trường `is_verified` vào bảng users (mặc định False).
- Alembic migration: `0003_add_is_verified_to_users.py`.

## 6. Lưu ý vận hành

- Cần cấu hình SMTP đúng, dùng App Password nếu là Gmail.
- Khởi động lại backend sau khi sửa .env.
- OTP được hash trước khi lưu Redis, không lưu plain text.
- Các API forgot/reset password không tiết lộ user có tồn tại hay không (bảo mật).

## 7. API mới

- `POST /auth/verify-email` — Xác thực email bằng OTP
- `POST /auth/resend-otp` — Gửi lại OTP xác thực email
- `POST /auth/change-password` — Đổi mật khẩu (yêu cầu JWT)
- `POST /auth/forgot-password` — Gửi OTP reset password
- `POST /auth/reset-password` — Đặt lại mật khẩu bằng OTP

## 8. Security

- OTP hash HMAC SHA256 trước khi lưu Redis
- Cooldown chống spam OTP qua Redis
- Không tiết lộ trạng thái user khi quên mật khẩu
- Chỉ user local mới đổi/quên mật khẩu qua các API này
