# API: Lấy thông tin user hiện tại (GET /users/me)

## Mô tả

Endpoint trả về thông tin profile của user đang đăng nhập, bọc trong trường `data`.

- **Method:** GET
- **Path:** `/api/v1/users/me`
- **Auth:** Bắt buộc (Bearer JWT)
- **Response model:**
  ```json
  {
    "data": {
      "id": "...",
      "username": "...",
      "email": "...",
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
  }
  ```

## Cách dùng

### Curl

```bash
curl -H "Authorization: Bearer <access_token>" \
     http://localhost:8000/api/v1/users/me
```

### FastAPI schema

- Wrapper: `UserMeDataResponse`
- Data: `UserMeResponse`

```python
class UserMeResponse(BaseModel):
    id: UUID
    username: str
    email: str
    role: str
    level_id: int
    xp: int
    streak_days: int
    trust_score: float
    onboarding_completed: bool
    is_banned: bool
    created_at: datetime
    updated_at: datetime

class UserMeDataResponse(BaseModel):
    data: UserMeResponse
```

### Route mẫu

```python
@router.get(
    "/me",
    response_model=UserMeDataResponse,
    summary="Lấy thông tin user hiện tại",
)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserMeDataResponse:
    user = await service.get_me(current_user.id)
    return UserMeDataResponse(data=UserMeResponse.model_validate(user))
```

## Lưu ý

- Nếu trả về `{ "data": ... }` thì response_model cũng phải là wrapper tương ứng.
- Nếu trả về trực tiếp user, dùng `response_model=UserMeResponse`.
- Nếu không truyền token hoặc token sai sẽ trả về 401.
