# Social Module (MVP)

## Endpoints

- `GET /api/v1/social/feed`
- `POST /api/v1/social/posts`
- `DELETE /api/v1/social/posts/{post_id}`
- `POST /api/v1/social/posts/{post_id}/like`
- `DELETE /api/v1/social/posts/{post_id}/like`
- `POST /api/v1/social/posts/{post_id}/comments`
- `GET /api/v1/social/posts/{post_id}/comments`
- `DELETE /api/v1/social/comments/{comment_id}`
- `POST /api/v1/social/users/{user_id}/follow`
- `DELETE /api/v1/social/users/{user_id}/follow`
- `GET /api/v1/social/users/{user_id}/followers`
- `GET /api/v1/social/users/{user_id}/following`

## Data Model

- `follows`: follower_id, following_id, created_at
- `posts`: id, submission_id (unique), user_id, like_count, comment_count, created_at
- `likes`: user_id, post_id, created_at
- `comments`: id, post_id, user_id, parent_id, content, is_deleted, created_at

## Notes

- Post gắn với `submission_id` (1-1), dùng lại ảnh/metadata từ submission.
- Comment xóa theo kiểu soft-delete (`is_deleted=true`).
- Feed lấy post của user và những người đang follow.
