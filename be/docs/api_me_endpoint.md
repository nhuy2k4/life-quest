# API: Lấy thông tin user hiện tại (`/me`)

## 1. Tổng quan

Các endpoint này trả về profile đầy đủ của user đang đăng nhập (dựa trên access token JWT). Có 2 đường dẫn tương đương:

- `GET /api/v1/users/me`
- `GET /api/v1/auth/me`

## 2. Yêu cầu xác thực

- Cần gửi header: `Authorization: Bearer <access_token>`
- Nếu token không hợp lệ hoặc hết hạn sẽ trả về 401.

## 3. Định nghĩa endpoint

### `GET /api/v1/users/me`

### `GET /api/v1/auth/me`

- **Method:** GET
- **Auth:** Bắt buộc (Bearer JWT)
- **Response:**
  - 200: Trả về thông tin user dạng `UserMeResponse`
  - 401: Không có hoặc token không hợp lệ
  - 404: User không tồn tại (hiếm gặp)

#### Response mẫu

```json
{
  "id": "b1e2c3d4-5678-1234-9abc-1234567890ab",
  "username": "huybui",
  "email": "huy@example.com",
  "role": "user",
  "level_id": 1,
  "xp": 100,
  "streak_days": 5,
  "trust_score": 1.0,
  "onboarding_completed": true,
  "is_banned": false,
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-04-01T10:00:00"
}
```

## 4. Sử dụng thử với curl

```bash
curl -H "Authorization: Bearer <access_token>" \
     http://localhost:8000/api/v1/users/me
```

hoặc

```bash
curl -H "Authorization: Bearer <access_token>" \
     http://localhost:8000/api/v1/auth/me
```

```

## 5. Ghi chú
- Hai endpoint này trả về dữ liệu giống nhau, chỉ khác path để tiện cho frontend hoặc mobile gọi theo module.
- Nếu không thấy trên Swagger UI, kiểm tra lại biến môi trường `DEBUG=True`.
```
