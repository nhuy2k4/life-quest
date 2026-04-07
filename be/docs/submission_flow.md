# Submission Flow

## Overview

Submission là bằng chứng người dùng nộp để hoàn thành quest. Admin có thể duyệt hoặc từ chối submission. Quy trình này đảm bảo rằng trạng thái của quest và XP của người dùng được đồng bộ hóa chính xác.

## API Endpoints

### 1. Approve Submission

- **Endpoint:** `PATCH /api/v1/admin/submissions/{submission_id}/approve`
- **Description:** Duyệt submission của người dùng.
- **Request Body:**
  ```json
  {}
  ```
- **Response:**
  ```json
  {
    "submission_id": "uuid",
    "status": "approved",
    "xp_granted": 100
  }
  ```

### 2. Reject Submission

- **Endpoint:** `PATCH /api/v1/admin/submissions/{submission_id}/reject`
- **Description:** Từ chối submission của người dùng.
- **Request Body:**
  ```json
  {
    "reason": "string"
  }
  ```
- **Response:**
  ```json
  {
    "submission_id": "uuid",
    "status": "rejected"
  }
  ```

### 3. List Submissions

- **Endpoint:** `GET /api/v1/admin/submissions`
- **Description:** Lấy danh sách các submission với bộ lọc trạng thái.
- **Query Parameters:**
  - `status` (optional): `pending`, `approved`, `rejected`
  - `page` (optional): Số trang (mặc định: 1)
  - `page_size` (optional): Số lượng submission mỗi trang (mặc định: 20)
- **Response:**
  ```json
  {
    "items": [
      {
        "submission_id": "uuid",
        "status": "pending",
        "user_id": "uuid",
        "quest_id": "uuid"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
  ```

## Database Changes

### 1. Bảng `XpTransaction`

- **Columns:**
  - `id`: UUID (primary key)
  - `user_id`: UUID (foreign key đến bảng `users`)
  - `submission_id`: UUID (foreign key đến bảng `submissions`, unique)
  - `amount`: Số XP được cấp
  - `source`: Enum (`quest_approved`, ...)
  - `created_at`: Timestamp
- **Purpose:** Đảm bảo XP chỉ được cấp một lần cho mỗi submission.

### 2. Enum Changes

- **SubmissionStatus:**
  - `pending`
  - `approved`
  - `rejected`
- **UserQuestStatus:**
  - `not_started`
  - `started`
  - `submitted`
  - `approved`
  - `rejected`

## Business Logic

### 1. Approve Submission

- **Steps:**
  1. Lấy submission từ database.
  2. Kiểm tra trạng thái submission:
     - Nếu đã `approved` hoặc `rejected`, trả về lỗi (409 Conflict).
  3. Cập nhật trạng thái submission thành `approved`.
  4. Cập nhật trạng thái quest của người dùng thành `approved`.
  5. Gọi `XpService` để cấp XP (idempotent).
  6. Lưu thay đổi vào database.

### 2. Reject Submission

- **Steps:**
  1. Lấy submission từ database.
  2. Kiểm tra trạng thái submission:
     - Nếu đã `approved` hoặc `rejected`, trả về lỗi (409 Conflict).
  3. Cập nhật trạng thái submission thành `rejected`.
  4. Cập nhật trạng thái quest của người dùng thành `rejected`.
  5. Lưu lý do từ chối vào database.
  6. Lưu thay đổi vào database.

### 3. List Submissions

- **Steps:**
  1. Lấy danh sách submission từ database với bộ lọc trạng thái (nếu có).
  2. Phân trang kết quả theo `page` và `page_size`.
  3. Trả về danh sách submission và tổng số lượng.

## Error Handling

- **409 Conflict:**
  - Khi submission đã được duyệt hoặc từ chối.
- **422 Unprocessable Entity:**
  - Khi request body không hợp lệ.
- **404 Not Found:**
  - Khi submission không tồn tại.
