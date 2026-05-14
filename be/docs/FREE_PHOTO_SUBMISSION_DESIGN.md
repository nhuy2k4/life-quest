# Free Photo Submission Design

## 1. Goal

Thiết kế lại luồng submission để user có thể gửi ảnh ngay mà không cần chọn quest trước.

Mục tiêu:

- Giảm friction: chụp/chọn ảnh -> gửi.
- Giữ kiến trúc monolith và tái sử dụng bảng hiện có.
- AI chỉ làm label detection nhẹ, không quyết định thay rule engine.

Constraints:

- Không thay đổi schema lớn.
- Tái sử dụng `submissions`, `quests`, `user_quests`.
- Không thêm AI logic nặng.

## 2. High-Level Backend Flow

### 2.1 Submit Free Photo

1. Client gọi endpoint mới `POST /api/v1/submissions/free` với ảnh.
2. Backend tạo bản ghi submission ở trạng thái `pending`.
3. Backend trả ngay response optimistic:

- `submission_id`
- `optimistic_status=likely_success` hoặc `under_review`
- `matched_quests=[]` tạm thời (nếu chưa kịp match sync)

4. Async pipeline chạy theo `submission_id`:

- Trích xuất metadata cơ bản (hash, exif basic)
- AI label detection (labels + confidence)
- Map labels -> quest candidates
- Tính điểm match nhẹ + anti-cheat nhẹ + trust_score
- Sinh decision set: `matched_quests`, `best_match`, `final_status_candidate`

5. Kết quả xử lý:

- Nếu có quest match tốt: gợi ý auto-assign hoặc để user chọn.
- Nếu không có match:
  - fallback Generic Quest
  - hoặc chuyển thành social post thường.

### 2.2 Match Then Confirm

Sau khi pipeline có kết quả, có 2 mode:

Mode A (auto-assign):

- Nếu `best_match_score >= AUTO_ASSIGN_THRESHOLD` và không suspicious.
- Tự tạo `user_quest` cho quest tốt nhất và gắn submission vào flow quest đó.

Mode B (user-select):

- Trả danh sách quest phù hợp.
- User chọn quest qua endpoint confirm.

## 3. API Proposal (Incremental)

## 3.1 New Endpoint: Free Submit

`POST /api/v1/submissions/free`

Request (simple):

- `image_file` hoặc `image_url`.

Response ngay:

```json
{
  "submission_id": "uuid",
  "submission_status": "pending",
  "optimistic_status": "likely_success",
  "match_status": "processing",
  "message": "Da nhan anh, dang tim quest phu hop"
}
```

## 3.2 Get Match Result

`GET /api/v1/submissions/{submission_id}/matches`

Response:

```json
{
  "submission_id": "uuid",
  "match_status": "ready",
  "best_match": {
    "quest_id": "uuid",
    "score": 0.82,
    "auto_assign_eligible": true
  },
  "matched_quests": [
    { "quest_id": "uuid", "title": "Check-in cafe", "score": 0.82 },
    { "quest_id": "uuid", "title": "Morning coffee", "score": 0.74 }
  ],
  "fallback": "none"
}
```

## 3.3 Confirm Assignment (User Select)

`POST /api/v1/submissions/{submission_id}/assign-quest`

Request:

```json
{
  "quest_id": "uuid"
}
```

Behavior:

- Tạo hoặc cập nhật `user_quest` ở trạng thái phù hợp.
- Gắn submission vào quest được chọn.

## 3.4 Fallback Actions

`POST /api/v1/submissions/{submission_id}/fallback`

Request:

```json
{
  "action": "generic_quest"
}
```

Hoặc:

```json
{
  "action": "social_post"
}
```

## 4. Quest Matching Strategy (Simple)

### 4.1 Lightweight Label Mapping

Sử dụng map cấu hình trong service layer:

- `label_to_category`
- `category_to_quests` (đọc từ `quest_categories` + `quests.is_active=true`)

Ví dụ:

- `cafe` -> `Giai tri`
- `food` -> `Suc khoe`, `Giai tri`
- `outdoor` -> `The thao`

### 4.2 Match Score

Match score đơn giản:

- 50% label overlap score
- 30% quest recency/popularity weight (nếu có)
- 20% trust-adjusted confidence

AI confidence chỉ đóng vai trò phụ.

## 5. Pseudo-Code

```python
def free_submit(user_id, image_input):
    submission = create_submission_pending(user_id=user_id, image=image_input)
    enqueue_match_pipeline(submission.id)
    return {
        "submission_id": submission.id,
        "submission_status": "pending",
        "optimistic_status": "likely_success",
        "match_status": "processing",
    }


def process_match_pipeline(submission_id):
    submission = get_submission(submission_id)
    user = get_user(submission.user_id)

    metadata = extract_basic_metadata(submission.image)
    anti_cheat = basic_anti_cheat(metadata)

    ai = detect_labels(submission.image)  # {labels, confidence}
    candidate_quests = map_labels_to_quests(ai.labels)

    ranked = rank_candidates(candidate_quests, ai.confidence, user.trust_score)

    if anti_cheat.suspicious:
        save_match_result(submission_id, status="manual_review", matched_quests=ranked)
        return

    if not ranked:
        save_match_result(submission_id, status="no_match", fallback="generic_or_social")
        return

    best = ranked[0]
    auto_assign_ok = best.score >= 0.8 and user.trust_score >= 0.6

    save_match_result(
        submission_id,
        status="ready",
        matched_quests=ranked,
        best_match=best,
        auto_assign_eligible=auto_assign_ok,
    )

    if auto_assign_ok:
        assign_submission_to_quest(submission_id, best.quest_id, mode="auto")
```

## 6. Minimal DB Changes

Không đổi cấu trúc lớn. Có 2 hướng:

### Option A (No migration, nhanh nhất)

Lưu kết quả match tạm vào Redis cache theo key:

- `submission_match:{submission_id}`

Ưu điểm:

- Không đụng DB schema.
- Triển khai nhanh.

Nhược điểm:

- Dữ liệu match không lưu dài hạn nếu cache expire.

### Option B (1 cột JSON nhẹ trong submissions)

Thêm tối đa 1 cột nullable:

- `match_snapshot JSON NULL`

Nội dung ví dụ:

```json
{
  "labels": ["cafe", "food"],
  "best_match_quest_id": "uuid",
  "matched_quests": [{ "quest_id": "uuid", "score": 0.82 }],
  "fallback": "none"
}
```

Khuyến nghị:

- Bắt đầu Option A.
- Nếu cần audit sản phẩm thì nâng lên Option B.

## 7. Reuse Existing Tables

`submissions`:

- vẫn là bản ghi gốc cho ảnh user gửi.

`quests`:

- là nguồn quest candidates sau bước map labels.

`user_quests`:

- chỉ tạo khi auto-assign hoặc user confirm chọn quest.

Rule quan trọng:

- Không tạo `user_quest` hàng loạt trước khi biết user sẽ chọn quest nào.

## 8. Fallback Policy

Khi không match quest:

- Fallback 1: gán vào Generic Quest (vd: "Daily Check-in Photo").
- Fallback 2: cho user đăng social post thường.

Điều kiện chọn fallback:

- Nếu user đang trong flow gamification -> ưu tiên Generic Quest.
- Nếu user chỉ muốn chia sẻ -> ưu tiên Social Post.

## 9. Frontend UX Flow (Minimal)

1. User mở camera/gallery.
2. User submit ảnh (không chọn quest trước).
3. UI hiển thị ngay "Dang tim quest phu hop...".
4. Poll endpoint matches mỗi 2-3 giây (tối đa 20-30 giây).
5. Khi có kết quả:

- Nếu auto-assign đủ điều kiện: hiển thị "Da gan vao quest X".
- Nếu nhiều lựa chọn: hiển thị list quest để user chọn 1.
- Nếu no-match: hiển thị 2 CTA:
  - "Dung Generic Quest"
  - "Dang nhu bai viet thuong"

UX rules:

- Không block UI khi chờ AI.
- Luôn có đường đi thành công (quest hoặc social).

## 10. Rollout Plan

Phase 1:

- Build free submit endpoint + processing status + no-match fallback.

Phase 2:

- Add lightweight AI label matching + user-select confirm.

Phase 3:

- Enable auto-assign cho high trust users theo feature flag.

## 11. Acceptance Checklist

- [ ] User có thể submit ảnh mà không chọn quest trước.
- [ ] Hệ thống trả matched quests sau xử lý async.
- [ ] User có thể chọn quest hoặc để auto-assign.
- [ ] Có fallback generic quest/social post khi no-match.
- [ ] Không thay đổi schema lớn và vẫn dùng `submissions`, `quests`, `user_quests`.
- [ ] AI vẫn chỉ là detector (labels + confidence).
