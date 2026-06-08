# Tổng hợp yêu cầu tạo báo cáo Đồ án Tốt nghiệp

## 1. Vai trò

Đóng vai trò là giảng viên hướng dẫn Đồ án Tốt nghiệp ngành Công nghệ thông tin của Đại học Bách Khoa.

Nhiệm vụ chính:

- Phân tích toàn bộ source code.
- Phân tích cấu trúc dự án.
- Phân tích database schema.
- Phân tích API.
- Phân tích tài liệu kỹ thuật.
- Phân tích ảnh giao diện và các file liên quan.
- Trích xuất dữ liệu phục vụ viết báo cáo Đồ án Tốt nghiệp.

## 2. Mục tiêu

Đọc toàn bộ project và tạo ra một bộ dữ liệu hoàn chỉnh để viết báo cáo ĐATN theo cấu trúc chuẩn của Đại học Bách Khoa Đà Nẵng.

Nguyên tắc bắt buộc:

- Không suy đoán nếu không có dữ liệu.
- Không tự bịa chức năng.
- Ưu tiên dữ liệu thực tế từ source code hơn mô tả.
- Nếu thiếu thông tin, ghi rõ theo mẫu:

```text
[MISSING INFORMATION]

- Nội dung còn thiếu
- File cần kiểm tra
- Thông tin sinh viên cần bổ sung
```

## 3. Cấu trúc đầu ra Markdown

---

# 1. THÔNG TIN HÀNH CHÍNH

## 1.1 Tên đề tài

## 1.2 Sinh viên thực hiện

## 1.3 Giảng viên hướng dẫn

## 1.4 Tóm tắt đề tài

Tạo bản tóm tắt 300-500 từ dựa trên chức năng thực tế của hệ thống.

---

# 2. PHẦN MỞ ĐẦU

## 2.1 Lý do chọn đề tài

Phân tích:

- Bài toán thực tế.
- Nhu cầu người dùng.
- Các hệ thống tương tự.
- Hạn chế hiện tại.

## 2.2 Mục tiêu đề tài

### Mục tiêu tổng quát

### Mục tiêu cụ thể

## 2.3 Phạm vi nghiên cứu

### Trong phạm vi

### Ngoài phạm vi

## 2.4 Phương pháp nghiên cứu

---

# 3. CHƯƠNG 1 - CƠ SỞ LÝ THUYẾT

Tự động phát hiện và mô tả các nội dung sau.

## 3.1 Kiến trúc hệ thống

Ví dụ:

- Client Server.
- RESTful Architecture.
- Layered Architecture.
- Clean Architecture.
- MVC.
- Microservice.
- Monolith.

## 3.2 Công nghệ Frontend

Ví dụ:

- React Native.
- Expo.
- TypeScript.
- Redux.
- Navigation.

## 3.3 Công nghệ Backend

Ví dụ:

- FastAPI.
- SQLAlchemy.
- Alembic.
- Celery.
- Redis.
- JWT.

## 3.4 Database

Phân tích:

- PostgreSQL.
- Quan hệ dữ liệu.
- Ưu điểm.

## 3.5 AI và Machine Learning

Nếu có, phân tích:

- Google Vision API.
- Recommendation System.
- Logistic Regression.
- AI Moderation.
- AI Validation.

## 3.6 DevOps

Ví dụ:

- Docker.
- Git.
- GitHub.
- CI/CD.

---

# 4. CHƯƠNG 2 - PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG

## 4.1 Yêu cầu chức năng

Tự động trích xuất từ source code.

Mỗi chức năng cần có:

- Tên chức năng.
- Mô tả.
- API liên quan.
- Màn hình liên quan.

Ví dụ các chức năng cần kiểm tra:

- Đăng ký.
- Đăng nhập.
- Quản lý hồ sơ.
- Hệ thống Quest.
- Hệ thống Badge.
- Hệ thống XP.
- Hệ thống Leaderboard.
- Hệ thống Recommendation.
- Hệ thống AI Review.
- Hệ thống Social Feed.
- Hệ thống Follow.
- Hệ thống Comment.
- Hệ thống Notification.

## 4.2 Yêu cầu phi chức năng

Phân tích:

- Hiệu năng.
- Bảo mật.
- Khả năng mở rộng.
- Tính khả dụng.
- Tính nhất quán dữ liệu.

## 4.3 Tác nhân hệ thống

Tự động phát hiện actor, ví dụ:

- Guest.
- User.
- Admin.
- AI Service.
- Notification Service.

## 4.4 Use Case

Cần sinh:

- Danh sách Use Case.
- Mô tả từng Use Case.

Mỗi Use Case gồm:

- Tên.
- Actor.
- Điều kiện tiên quyết.
- Luồng chính.
- Luồng thay thế.
- Kết quả.

## 4.5 Activity Diagram

Tạo PlantUML cho:

- Đăng nhập.
- Hoàn thành Quest.
- AI xét duyệt ảnh.
- Tạo bài đăng.
- Nhận Badge.

## 4.6 Sequence Diagram

Tạo PlantUML cho:

- Login.
- Quest Flow.
- Submission Flow.
- AI Approval Flow.
- Recommendation Flow.

## 4.7 Database Design

Phân tích toàn bộ schema.

Với mỗi bảng, cần có:

### Tên bảng

### Chức năng

### Danh sách cột

| Tên cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa |
| --- | --- | --- | --- |

### Quan hệ

Sau đó sinh:

- ERD dạng Mermaid.
- ERD dạng PlantUML.

---

# 5. CHƯƠNG 3 - TRIỂN KHAI VÀ KIỂM THỬ

## 5.1 Môi trường triển khai

Phân tích:

- Backend.
- Frontend.
- Database.
- Cloud.
- AI Service.

## 5.2 Chức năng đã triển khai

Với mỗi chức năng, cần có:

- Mô tả.
- API.
- Screenshot cần chụp.

## 5.3 Danh sách màn hình

Tự động phát hiện từ source frontend.

Ví dụ:

- Login Screen.
- Home Screen.
- Quest Screen.
- Quest Detail.
- Profile.
- Leaderboard.
- Badge.
- Notification.

## 5.4 Test Case

Tạo bảng test case tối thiểu 30 trường hợp:

| ID | Chức năng | Input | Kết quả mong muốn | Kết quả thực tế | Status |
| --- | --- | --- | --- | --- | --- |

---

# 6. KẾT LUẬN

## 6.1 Kết quả đạt được

## 6.2 Ưu điểm hệ thống

## 6.3 Hạn chế

## 6.4 Hướng phát triển

Đề xuất các hướng mở rộng thực tế.

---

# 7. TÀI LIỆU THAM KHẢO

Tự động tạo danh sách tài liệu tham khảo dựa trên công nghệ phát hiện trong project.

Ví dụ:

- FastAPI Documentation.
- PostgreSQL Documentation.
- React Native Documentation.
- SQLAlchemy Documentation.
- Google Vision API Documentation.
- JWT RFC.
- REST API Design Guide.

---

# 8. DANH SÁCH THÔNG TIN CÒN THIẾU

Liệt kê toàn bộ dữ liệu còn thiếu để hoàn thiện báo cáo 100%.

Ví dụ:

- Thông tin sinh viên.
- Tên giảng viên.
- Ảnh giao diện.
- Thông số server.
- Kết quả benchmark.
- Nhật ký kiểm thử.

---

## 4. Yêu cầu đặc biệt

1. Phân tích dựa trên source code thực tế.
2. Không tự bịa chức năng.
3. Nếu phát hiện API thì liệt kê endpoint.
4. Nếu phát hiện database thì sinh ERD.
5. Nếu phát hiện React Native thì liệt kê màn hình.
6. Nếu phát hiện FastAPI thì liệt kê router.
7. Nếu phát hiện Alembic thì phân tích migration.
8. Nếu phát hiện AI thì mô tả luồng AI chi tiết.
9. Ưu tiên dữ liệu thực tế từ source code hơn mô tả.
10. Cuối cùng xuất một checklist các mục đã đủ dữ liệu và các mục còn thiếu.

## 5. Checklist đầu ra cần có

- [ ] Thông tin hành chính.
- [ ] Tóm tắt đề tài 300-500 từ.
- [ ] Lý do chọn đề tài.
- [ ] Mục tiêu tổng quát và mục tiêu cụ thể.
- [ ] Phạm vi nghiên cứu.
- [ ] Phương pháp nghiên cứu.
- [ ] Cơ sở lý thuyết theo công nghệ thực tế.
- [ ] Kiến trúc hệ thống.
- [ ] Danh sách chức năng trích xuất từ source code.
- [ ] Danh sách API endpoint.
- [ ] Danh sách màn hình frontend.
- [ ] Actor hệ thống.
- [ ] Use Case.
- [ ] Activity Diagram bằng PlantUML.
- [ ] Sequence Diagram bằng PlantUML.
- [ ] Database schema.
- [ ] ERD Mermaid.
- [ ] ERD PlantUML.
- [ ] Môi trường triển khai.
- [ ] Danh sách chức năng đã triển khai.
- [ ] Danh sách screenshot cần chụp.
- [ ] Tối thiểu 30 test cases.
- [ ] Kết luận.
- [ ] Tài liệu tham khảo.
- [ ] Danh sách thông tin còn thiếu.
