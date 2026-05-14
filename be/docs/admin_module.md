# Admin Module (MVP)

## Endpoints

- `GET /api/v1/admin/users`
- `PATCH /api/v1/admin/users/{user_id}/ban`
- `POST /api/v1/admin/users/{user_id}/xp-adjust`
- `GET /api/v1/admin/quests`
- `PATCH /api/v1/admin/quests/{quest_id}`
- `DELETE /api/v1/admin/posts/{post_id}`
- `DELETE /api/v1/admin/comments/{comment_id}`
- Admin submissions: `GET /api/v1/admin/submissions`, `PATCH /api/v1/admin/submissions/{id}/approve|reject`

## Notes

- Các endpoint yêu cầu role `admin`.
- XP adjust tạo `xp_transactions` với `source=admin_adjust`.
- Audit log được ghi cho hành động ban user, cập nhật quest, xóa post/comment, điều chỉnh XP.
