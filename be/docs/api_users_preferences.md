# API: User Preferences

## 1. Lấy preferences hiện tại

### GET /api/v1/users/me/preferences

- **Auth:** Bắt buộc (Bearer JWT)
- **Response:**

```json
{
  "data": {
    "interests": [1, 2, 3],
    "interest_weights": { "1": 0.7, "2": 0.2 },
    "activity_level": "medium",
    "location_enabled": true,
    "notification_enabled": true
  }
}
```

- **Schema:** `PreferenceResponse`

## 2. Tạo/cập nhật preferences

### POST /api/v1/users/me/preferences

- **Auth:** Bắt buộc (Bearer JWT)
- **Body:**

```json
{
  "interests": [1, 2, 3],
  "activity_level": "medium",
  "location_enabled": true
}
```

- **Schema:** `PreferenceRequest`
- **Response:**

```json
{
  "data": {
    "interests": [1, 2, 3],
    "interest_weights": { "1": 0.7, "2": 0.2 },
    "activity_level": "medium",
    "location_enabled": true,
    "notification_enabled": true
  }
}
```

- Khi cập nhật thành công sẽ tự động set `onboarding_completed=true` cho user.

## 3. Schema mẫu

```python
class PreferenceRequest(BaseModel):
    interests: list[int]
    activity_level: str
    location_enabled: bool = True

class PreferenceResponse(BaseModel):
    interests: list[int]
    interest_weights: dict
    activity_level: str | None = None
    location_enabled: bool
    notification_enabled: bool
    model_config = {"from_attributes": True}
```

## 4. Lưu ý

- Nếu user chưa có preferences sẽ trả 404.
- Khi cập nhật sẽ invalidate recommendation cache (nếu có).
- Các trường hợp lỗi sẽ trả về HTTP 400/404 chuẩn hóa.
