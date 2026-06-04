# Tóm tắt hoàn thành — Recommendation V2 MVP (2026-05-07)

**Mục tiêu ngắn gọn:**

- Triển khai MVP hệ thống đề xuất Recommendation V2 (hybrid: rule-based + 1 ML ranker sau này) với tính năng explainability, logging và chuẩn bị dữ liệu cho huấn luyện offline.

**Tổng quan đã hoàn thành:**

- Thiết kế và cài đặt pipeline đề xuất giải thích được (explainable): tạo candidate, áp dụng rule scoring, rerank để đảm bảo đa dạng và cooldown.
- Thêm bảng và migration cho logging, thống kê hàng ngày và điểm trending (Alembic migration `0018` đã tạo và áp dụng).
- Sửa migration seed (0017) để tránh lỗi JSON/timestamp khi chạy Alembic.
- Thêm API và schema:
  - `GET /recommendations/quests` trả về `request_id`, `score_breakdown` và `reasons` cho mỗi quest.
  - `POST /recommendations/log` để client ghi lại event (shown/click/started/completed).
- Implement service core `recommendation_service.py` với:
  - Candidate generation (trending, social, category, recent, exploration).
  - Cooldown filtering, explainable rule scoring với mã lý do và breakdown điểm.
  - Diversity rerank (hạn chế số quest cùng category), pagination và logging shown events.
- Thêm Celery maintenance tasks và cấu hình Celery Beat để chạy các job tính toán thống kê/trending định kỳ.
- Cập nhật và chạy unit tests liên quan; tests cho recommendation đã chạy pass (4/4) cục bộ.

**Các file/điểm thay đổi chính:**

- **Models / DB:** app/models/recommendation.py (RecommendationLog). Legacy stats tables were removed; ranking now derives directly from recommendation logs, posts, user quests, and quest categories.
- **Migrations:** app/migrations/versions/0018_recommendation_v2_tables.py (tạo bảng mới) và điều chỉnh 0017_seed_ai_quests.py (fix JSON/timestamp)
- **Schemas:** app/schemas/recommendation.py (thêm request_id, reasons enum, score_breakdown, log request schema)
- **Service:** app/services/recommendation/recommendation_service.py (candidate gen, scoring, rerank, logging)
- **API:** app/api/v1/recommendations.py (GET + POST log endpoints)
- **Workers:** app/workers/maintenance_tasks.py, app/workers/celery_app.py (task + beat schedule)
- **Tests:** tests/test_recommendation.py (cập nhật và pass local)

**Vấn đề đã xử lý:**

- Fix Alembic seed errors: truyền JSON/list đúng kiểu và dùng timestamp UTC naive để tránh lỗi asyncpg.
- Điều chỉnh Pydantic schema/serialization (UUID, trường `request_id`) để tests và API hoạt động.

**Công việc còn dở / đề xuất tiếp theo:**

- Xây pipeline offline cho huấn luyện ML (export logs → feature engineering → train LR/XGBoost) và lưu model.
- Tích hợp inference model (nhẹ) vào `recommendation_service` khi model sẵn sàng.
- Thêm endpoint admin/cron trigger, dashboard KPIs, và retention policy cho logs.
- Triển khai Celery worker + beat trong production (container/service orchestration).
- FE: tích hợp gửi event đầy đủ (shown/click/started/completed) tới `POST /recommendations/log`.

**Ghi chú triển khai:**

- Stack: FastAPI + SQLAlchemy async + Alembic + PostgreSQL (prod) + Redis + Celery.
- Thiết kế ưu tiên explainability và khả năng tạo dataset cho huấn luyện offline trước khi đưa ML vào sản xuất.

_File này được tạo tự động bởi bot để tóm tắt tiến độ làm việc. Nếu bạn muốn mở rộng nội dung (ví dụ: chi tiết schema, ví dụ payload, hoặc lộ trình ML), bảo tôi cập nhật thêm._
