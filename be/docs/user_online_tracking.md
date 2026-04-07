# Cơ Chế Theo Dõi Trạng Thái Online của User

## Tổng quan

Tài liệu này giải thích cách backend theo dõi trạng thái online của user bằng Redis và middleware, đồng thời mô tả thay đổi mới giúp cơ chế này ổn định, dễ bảo trì hơn.

## Cách hoạt động

1. **OnlineTrackingMiddleware**
   - Được add vào FastAPI app.
   - Sau mỗi request đã xác thực, middleware sẽ gọi `mark_user_online_from_state` để đánh dấu user online nếu có thông tin user trong request state.

2. **Truyền user_id vào request.state**
   - Các dependency xác thực (`get_current_user`, `get_current_user_optional`) sẽ tự động gán `request.state.user_id = user.id` sau khi xác thực thành công.
   - Đảm bảo mọi endpoint có xác thực đều cung cấp user_id cho middleware tracking online, không cần gán thủ công ở từng route.

3. **Đánh dấu user online**
   - Nếu có user_id, middleware sẽ set key Redis: `user:online:{user_id}` với giá trị "1" và TTL (thời gian sống) là 60 giây.
   - Mỗi request xác thực mới sẽ reset TTL, giữ trạng thái online liên tục nếu user còn hoạt động.

4. **Kiểm tra trạng thái online**
   - Endpoint `/api/v1/users/{user_id}/online` kiểm tra sự tồn tại của key Redis này để xác định user có online hay không.
   - Nếu key còn tồn tại (TTL > 0), user được coi là online; ngược lại là offline.

## Lợi ích của giải pháp này

- **Ổn định:** Middleware luôn nhận được user_id cho mọi request xác thực, tracking online nhất quán.
- **Dễ bảo trì:** Không cần sửa từng route để hỗ trợ tracking online.
- **Hiệu quả:** Sử dụng Redis, tối ưu cho thao tác key-value nhanh.
- **Gần real-time:** TTL giúp trạng thái online cập nhật gần như tức thời.

## Lưu ý

- TTL mặc định là 60 giây (có thể chỉnh sửa).
- Cách này chỉ kiểm tra user có online trong cửa sổ TTL gần nhất, không lưu lịch sử online.
- Nếu hệ thống có traffic cực lớn, có thể tối ưu thêm (ví dụ: chỉ reset TTL nếu sắp hết hạn).

## Tóm tắt thay đổi gần đây

Dependency xác thực sẽ tự động gán `request.state.user_id`, giúp tracking online tự động, ổn định cho mọi endpoint xác thực.
