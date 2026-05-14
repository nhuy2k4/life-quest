# LifeQuest Refinement Rulebook

## 1. Purpose

Tài liệu này là bộ rule bắt buộc khi triển khai cải tiến hệ thống LifeQuest trong tương lai.

Mục tiêu:

- Tăng trải nghiệm người dùng (ít chờ, ít thao tác).
- Tăng độ ổn định hệ thống (không phụ thuộc AI để quyết định cuối).
- Tăng engagement (streak, quest dễ, thông báo tiến độ).

Phạm vi:

- Áp dụng cho backend monolith FastAPI + PostgreSQL + Celery hiện tại.
- Thay đổi theo hướng incremental, an toàn, tương thích ngược.

Không làm:

- Không tách microservices.
- Không xóa core tables.
- Không thay đổi schema theo hướng phá vỡ dữ liệu cũ.

Tài liệu triển khai liên quan:

- Free photo submission (không chọn quest trước): `docs/FREE_PHOTO_SUBMISSION_DESIGN.md`

## 2. Core Principles (MUST)

1. AI chỉ là tín hiệu, không phải người ra quyết định cuối.
2. Phản hồi submit phải nhanh và có cảm giác "được ghi nhận ngay".
3. Rule-based decision + trust_score là tuyến quyết định chính.
4. Ưu tiên fallback an toàn: nghi ngờ thì manual_review, không auto reject quá sớm.
5. Triển khai theo feature flag để rollback nhanh.

## 3. Decision Model Rules

## 3.1 AI Role (MUST)

AI service chỉ được trả về:

- labels: danh sách nhãn ngữ cảnh (vd: cafe, food, outdoor)
- ai_confidence: độ tin cậy 0..1

AI KHONG duoc:

- Trực tiếp set approved/rejected.
- Trực tiếp cấp XP.

Final decision bắt buộc dùng:

- rule_score (anti-cheat + quest match)
- trust_score (theo user)
- ai_confidence (chỉ là hệ số hỗ trợ)

## 3.2 Trust Score Policy (MUST)

Quy ước trust tiers:

- High trust: trust_score >= 0.8
- Medium trust: 0.4 <= trust_score < 0.8
- Low trust: trust_score < 0.4

Chính sách:

- High trust: giảm ngưỡng approve, giảm xác suất manual_review.
- Medium trust: ngưỡng chuẩn.
- Low trust: tăng ngưỡng approve, tăng manual_review.

Trust score không được dùng một mình để approve.

## 4. Submission UX Rules

## 4.1 Instant Feedback (CRITICAL, MUST)

Ngay sau submit API phải trả response thành công nhanh, không chờ AI async.

Response cần có:

- submission_id
- status_human: "likely_success" | "under_review"
- final_status: luôn bắt đầu từ "pending"
- message thân thiện (khong technical)

Nguyên tắc:

- "Likely success" la optimistic state cho UX, khong phai approved vinh vien.
- Nếu hậu kiểm fail: chuyển rejected/manual_review + gửi notification giải thích.

## 4.2 Friction Reduction (MUST)

Frontend flow chuẩn:

- pick/take photo -> submit.

Backend tự xử lý:

- file_hash
- EXIF parse
- duplicate checks
- basic anti-cheat rules

Client không bắt buộc tự tính hash trước khi submit.

## 5. Updated Submission Flow (Target)

1. Client gửi ảnh (multipart hoặc signed-upload token + final submit).
2. API tạo Submission status=pending.
3. API trả ngay optimistic response (likely_success/under_review).
4. Async pipeline chạy:

- Collect metadata (hash, exif)
- Rule checks
- AI label extraction
- Quest matching validation
- Final decision (rule-based + trust_score)

5. Nếu approved:

- update submission/user_quest
- grant XP idempotent
- push progress notification

6. Nếu rejected/manual_review:

- update status + reason code
- push fallback notification

SLO UX:

- Submit API p95 < 800ms (khong cho AI).

## 6. Approval Logic (Pseudo Code)

```python
def decide_submission(submission, user, quest, ai_result, rule_result):
    # ai_result: {labels: list[str], ai_confidence: float}
    # rule_result: {rule_score: float, suspicious: bool, reason_codes: list[str]}

    trust = user.trust_score  # 0..1
    base_threshold = 0.65

    if trust >= 0.8:
        threshold = base_threshold - 0.10
        review_bias = 0.10
    elif trust < 0.4:
        threshold = base_threshold + 0.10
        review_bias = 0.40
    else:
        threshold = base_threshold
        review_bias = 0.20

    # AI is supportive only
    combined = 0.8 * rule_result.rule_score + 0.2 * ai_result.ai_confidence

    if rule_result.suspicious:
        return MANUAL_REVIEW, ["suspicious"] + rule_result.reason_codes

    if combined >= threshold:
        return APPROVED, []

    if combined >= (threshold - review_bias):
        return MANUAL_REVIEW, ["low_confidence"]

    return REJECTED, ["insufficient_evidence"]
```

Ràng buộc bắt buộc:

- AI confidence không vượt quá 20% trọng số quyết định cuối.
- suspicious=true luôn ưu tiên manual_review trước reject cứng.

## 7. Flexible Quest Matching Rules

Không thay đổi schema lớn. Dùng lớp mapping nhẹ:

- label_to_category_map trong config/service layer.
- category -> quests đã có qua quest_categories.

Ví dụ:

- label cafe -> category "Giải trí" hoặc "Xã hội" (theo config)
- category -> candidate quests -> kiểm tra quest active/user state.

Rule:

- Mapping là cấu hình, không hardcode trong controller.
- Thêm cache ngắn hạn (TTL) cho mapping đọc nhiều.

## 8. Anti-Cheat Simplification Rules

Giữ anti-cheat tối thiểu nhưng hiệu quả:

- Duplicate hash check.
- EXIF basic sanity (timestamp bất thường, metadata trống bất thường).
- Frequency guard (submit quá dày trong khoảng ngắn).

Bỏ/không làm sớm:

- Rule quá phức tạp khó explain cho user.
- Heuristic nhiều tầng không đo được hiệu quả.

Nguyên tắc:

- Mỗi rule anti-cheat phải có reason_code rõ ràng.
- reason_code phải map được sang message cho user/admin.

## 9. Celery Simplification Rules

Chỉ giữ task thực sự cần async:

- AI label extraction
- heavy metadata checks
- notification fan-out

Không đưa vào Celery các bước nhẹ có thể sync < 100ms.

Thiết kế queue đơn giản:

- queue: approval
- queue: notification

Task requirements:

- idempotent theo submission_id
- retry có backoff
- timeout rõ ràng
- log có correlation_id

## 10. API Change Rules (Incremental)

Giữ tương thích endpoint cũ, mở rộng response dần.

### 10.1 Submit

`POST /api/v1/quests/{quest_id}/submit`

Cho phép 2 mode:

- Legacy mode: giữ payload cũ.
- Simple mode: nhận file upload hoặc upload token.

Response mở rộng:

- submission_id
- submission_status (pending)
- optimistic_status (likely_success|under_review)
- next_check_after_seconds

### 10.2 Submission Detail

`GET /api/v1/submissions/{submission_id}`

Mở rộng field:

- decision_reason_codes: list[str]
- ai_labels: list[str] (optional)
- ai_confidence: float (optional)

## 11. Minimal Frontend Changes

Bắt buộc tối thiểu:

- Submit screen chỉ cần chụp/chọn ảnh và bấm gửi.
- Hiển thị ngay trạng thái optimistic (likely_success).
- Tự refresh/poll submission detail sau X giây.
- Nếu rejected/manual_review: hiển thị lý do thân thiện + CTA thử lại.

Nên có:

- Badge "Streak today" ở home.
- Progress card: "Con 1 quest de dat moc thuong".

## 12. Engagement Loop Rules

Mỗi submission event cần kích hoạt ít nhất 1 feedback loop:

- XP progress update
- streak status update
- notification theo tiến độ

Ưu tiên easy quests:

- low effort, high reward, hoàn thành nhanh trong 1-3 phút.
- dùng để tạo cảm giác thắng sớm cho user mới.

Notification rules:

- Không spam.
- Message theo ngữ cảnh tiến độ (không generic).

## 13. Observability & Safety

Mỗi quyết định phải trace được:

- submission_id
- trust tier
- rule_score
- ai_confidence
- final decision
- reason_codes

Đặt metric tối thiểu:

- approve rate
- manual review rate
- false reject appeal rate
- submit latency p95

## 14. Rollout Plan (Safe)

Phase 1:

- Thêm optimistic response + giữ admin approval như cũ.

Phase 2:

- Thêm async rule engine + AI labels.
- Final decision dùng rule + trust_score cho subset user (feature flag).

Phase 3:

- Mở rộng toàn bộ user.
- Tối ưu threshold theo dữ liệu thực tế.

## 15. Definition of Done Checklist

- [ ] Submit API không chờ AI, phản hồi nhanh.
- [ ] AI chỉ trả labels + confidence.
- [ ] Final decision không phụ thuộc duy nhất vào AI.
- [ ] trust_score đã ảnh hưởng threshold + manual_review.
- [ ] Có fallback rõ khi optimistic sai.
- [ ] Anti-cheat có reason_code giải thích được.
- [ ] Celery tasks idempotent + retry/backoff.
- [ ] Frontend hiển thị optimistic + status update rõ ràng.
- [ ] Có metrics để đánh giá tác động sản phẩm.
