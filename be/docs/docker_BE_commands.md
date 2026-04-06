# Docker & Backend (BE) Command Cheat Sheet

## Docker Compose

- Khởi động các service (chạy nền):
  docker compose up -d

- Dừng toàn bộ service:
  docker compose down

- Dừng và xóa toàn bộ service + volume (xóa sạch dữ liệu DB):
  docker compose down -v

- Xem log các service:
  docker compose logs

- Xem log 1 service cụ thể (ví dụ db):
  docker compose logs db

- Xem trạng thái các container:
  docker compose ps

- Truy cập vào container PostgreSQL:
  docker compose exec db bash

- Truy cập psql trong container:
  docker compose exec db psql -U <user> -d <database>

## Backend (BE) Python

- Tạo virtual environment:
  python -m venv .venv

- Kích hoạt virtual environment (Windows):
  .venv\Scripts\activate

- Cài đặt package:
  pip install -r requirements.txt

- Chạy Alembic migration:
  alembic upgrade head
  hoặc python -m alembic upgrade head
- Tạo migration mới:
  alembic revision --autogenerate -m "Tên migration"

- Chạy FastAPI server (dev):
  uvicorn app.main:app --reload

## Khác

- Xem các volume Docker:
  docker volume ls

- Xóa volume cụ thể:
  docker volume rm <tên_volume>

- Xem các image Docker:
  docker images

- Xóa image cụ thể:
  docker rmi <image_id>

---

Thay <user>, <database>, <tên_volume>, <image_id> bằng giá trị thực tế của bạn.
