# Authentication System - Technical Summary

## 1. Kiến trúc tổng quan

- Sử dụng FastAPI, SQLAlchemy async, JWT cho xác thực.
- Access token: JWT, lưu trên client, kiểm tra blacklist trên Redis khi logout.
- Refresh token: Sinh ngẫu nhiên, lưu hash SHA256 trong bảng `refresh_tokens` (user_id, token_hash, is_revoked, expires_at).
- Mỗi lần refresh hoặc logout đều kiểm tra và thu hồi refresh token.

## 2. Quy trình xác thực

- **Đăng nhập:** Kiểm tra username/password, phát access token (JWT) và refresh token (lưu hash vào DB).
- **Làm mới token:** Refresh token rotation, mỗi lần refresh sẽ thu hồi token cũ, phát token mới.
- **Đăng xuất:** Thu hồi access token (đưa vào Redis blacklist) và refresh token (set is_revoked=True trong DB).

## 3. Bảo mật refresh token

- Hash refresh token bằng SHA256 (deterministic, không dùng bcrypt).
- Không bao giờ lưu raw refresh token trong DB.
- Khi nhận refresh token hoặc logout, luôn kiểm tra:
  - Nếu token không tồn tại hoặc đã bị revoke → trả về 401.
  - Nếu token đã bị revoke mà vẫn gửi lên → phát hiện reuse attack, thu hồi toàn bộ refresh token của user (revoke all), trả về 401.
- Chống reuse token: Nếu refresh token đã bị sử dụng (is_revoked=True) mà vẫn gửi lên, hệ thống coi là dấu hiệu bị đánh cắp và khóa toàn bộ session.

## 4. Các điểm nổi bật & best practices

- **Token rotation:** Refresh token chỉ dùng 1 lần, mỗi lần refresh sẽ phát token mới và thu hồi token cũ.
- **Token reuse detection:** Nếu token đã bị revoke mà vẫn gửi lên, hệ thống sẽ revoke toàn bộ refresh token của user để ngăn chặn attacker.
- **Async SQLAlchemy:** Toàn bộ thao tác DB đều dùng async/await, phù hợp với FastAPI.
- **Không trả lỗi chi tiết khi đăng nhập sai:** Tránh lộ thông tin cho attacker (username/password đều trả lỗi chung).
- **Access token blacklist:** Đảm bảo logout có hiệu lực ngay lập tức, không cần chờ token hết hạn.

## 5. Đề xuất mở rộng

- Có thể bổ sung thêm audit log khi phát hiện reuse attack.
- Có thể gửi cảnh báo bảo mật cho user khi bị khóa toàn bộ session.
