# Tổng hợp chức năng đã triển khai trong dự án LifeQuest

## 1. Tổng quan hệ thống

LifeQuest là ứng dụng mạng xã hội kết hợp gamification, nhiệm vụ chụp ảnh, AI đánh giá nội dung và hệ thống thành tựu. Người dùng có thể đăng ảnh, hoàn thành nhiệm vụ, nhận XP, mở khóa huy hiệu, tương tác với cộng đồng và khám phá các địa điểm POI gần mình.

Hệ thống gồm ba phần chính:

- Mobile app: ứng dụng React Native/Expo cho người dùng cuối.
- Backend: FastAPI xử lý nghiệp vụ, xác thực, quest, feed, AI, POI, XP, badge và notification.
- Admin web: giao diện quản trị dữ liệu hệ thống, POI, quest, badge và nội dung.

## 2. Xác thực và tài khoản người dùng

Hệ thống đã triển khai luồng tài khoản đầy đủ cho người dùng:

- Đăng ký tài khoản bằng email.
- Đăng nhập bằng username/password.
- Đăng nhập bằng Google.
- Xác thực email bằng OTP.
- Gửi lại mã OTP.
- Refresh token để duy trì phiên đăng nhập.
- Đăng xuất và xóa token cục bộ.
- Kiểm tra trạng thái onboarding sau khi đăng nhập.
- Phân quyền người dùng thường và admin.
- Chặn truy cập với tài khoản bị khóa hoặc chưa hoàn tất điều kiện cần thiết.

Trên mobile, trạng thái đăng nhập được hydrate từ local storage, tự động điều hướng vào đúng màn hình theo trạng thái đăng nhập và onboarding.

## 3. Onboarding và sở thích cá nhân

Ứng dụng có luồng onboarding để cá nhân hóa trải nghiệm ban đầu:

- Giới thiệu ứng dụng.
- Xin quyền cần thiết như camera và vị trí.
- Thiết lập thông tin ban đầu.
- Chọn nhóm sở thích.
- Lưu preferences lên backend.
- Đánh dấu người dùng đã hoàn tất onboarding.
- Dùng sở thích để hỗ trợ đề xuất nội dung và nhiệm vụ.

## 4. Hồ sơ người dùng

Hồ sơ người dùng đã bao gồm các chức năng chính:

- Xem thông tin cá nhân.
- Xem hồ sơ người dùng khác.
- Cập nhật thông tin profile.
- Hiển thị level, XP và tiến độ lên cấp.
- Hiển thị số bài đăng, streak và số nhiệm vụ đã hoàn thành.
- Hiển thị ảnh đã đăng và ảnh đã thích.
- Hiển thị huy hiệu/thành tựu đã mở khóa.
- Cấu hình featured badges trên profile.

## 5. Bài đăng và mạng xã hội

Ứng dụng hỗ trợ luồng mạng xã hội cơ bản:

- Tạo bài post tự do bằng ảnh.
- Tạo bài post gắn với quest/submission.
- Hiển thị feed bài viết.
- Xem chi tiết bài viết.
- Like/unlike bài viết.
- Bình luận bài viết.
- Follow/unfollow người dùng.
- Xóa bài viết của chính người dùng.
- Gắn thông tin quest vào bài post nếu bài post đến từ nhiệm vụ.
- Gắn thông tin POI/location vào bài post khi người dùng chọn.
- Hiển thị bài post vừa đăng lên đầu feed trong phiên hiện tại.

Feed đã có logic trộn nội dung để tránh việc reload luôn giữ nguyên một thứ tự cứng. Các bài mới trong ngày được ưu tiên, bài cũ có tương tác tăng mạnh vẫn có cơ hội nổi lên, sau đó feed tiếp tục được trộn theo rule.

## 6. Quest và vòng đời nhiệm vụ

Hệ thống quest đã được triển khai theo vòng đời đầy đủ:

- Danh sách nhiệm vụ đang hoạt động.
- Chi tiết nhiệm vụ.
- Bắt đầu nhiệm vụ.
- Lưu trạng thái nhiệm vụ theo user.
- Nộp ảnh hoàn thành nhiệm vụ.
- Theo dõi trạng thái: not_started, started, submitted, approved, rejected.
- Hỗ trợ retry khi submission bị rejected.
- Giới hạn số lần retry.
- Cập nhật submission/post cũ khi retry thay vì tạo nhiệm vụ hoặc bài post trùng không cần thiết.
- Tính XP thưởng theo nhiệm vụ.
- Hỗ trợ nhiệm vụ có giới hạn thời gian.
- Quest detail hiển thị XP cơ bản, XP bonus theo vị trí và tổng XP có thể nhận.

Một điểm quan trọng đã được hoàn thiện là phân biệt quest base và quest instance. Cùng một nhiệm vụ chụp ảnh đối tượng nhưng thực hiện ở các POI khác nhau sẽ được tính là các nhiệm vụ riêng biệt. Ví dụ chụp ảnh cây bút tại vị trí A và chụp ảnh cây bút tại vị trí B không bị tính chung; người dùng có thể hoàn thành ở A rồi tiếp tục làm ở B để nhận XP.

## 7. Quest Log trên mobile

Tab Quest trong bottom navigation đã được tổ chức thành các nhóm:

- Available: nhiệm vụ có thể làm.
- In Progress: nhiệm vụ đang làm hoặc đang chờ duyệt.
- Completed: nhiệm vụ đã hoàn thành.
- Failed: nhiệm vụ bị từ chối.

Quest Log đã hỗ trợ hiển thị cả quest base và quest instance theo POI. Các nhiệm vụ instance đã hoàn thành tại từng POI được đưa vào tab Completed riêng, có giữ `poi_id` để khi bấm vào mở đúng chi tiết nhiệm vụ tại địa điểm đó.

## 8. Camera và luồng đăng ảnh

Mobile app đã triển khai luồng camera và xử lý ảnh:

- Mở camera từ bottom nav.
- Chụp ảnh cho free post.
- Chụp ảnh cho quest.
- Xem màn hình kết quả sau khi chụp.
- Upload ảnh.
- Tính hash ảnh để hỗ trợ kiểm tra submission.
- Tạo post sau khi upload.
- Nộp quest kèm ảnh, vị trí và POI nếu có.
- Phân biệt rõ camera free post và camera quest.
- Khi chuyển từ quest sang free post, app không tự giữ lại quest cũ.
- Khi retry quest, app giữ liên kết submission/post đúng.

Flow free post không tự ý gắn nhiệm vụ cũ. Với vị trí/POI, free post chỉ gợi ý cho người dùng gắn, không tự gắn mặc định.

## 9. Vị trí và POI

Hệ thống POI/location đã được triển khai ở cả backend, mobile và admin:

- Lấy vị trí khi mở app hoặc vào Home.
- Lấy vị trí khi vào Explore hoặc Quest Detail.
- Làm nóng cache vị trí khi mở Camera.
- Refresh vị trí khi Submit nếu vị trí cũ.
- Lưu location cache phía mobile để tránh hỏi/lấy vị trí quá nhiều lần.
- Gửi `lat`, `lng`, `accuracy_m` lên backend khi cần gợi ý POI.
- Backend gợi ý POI dựa trên bán kính POI và độ chính xác GPS.
- Log thông tin hỗ trợ kiểm tra vì sao có/không có POI suggestion.
- Free post hiển thị POI suggestion để người dùng chủ động gắn.
- Quest có POI cố định giữ đúng POI của nhiệm vụ.

Admin POI Manager đã có thêm chức năng hiển thị vị trí hiện tại của admin trên bản đồ, giúp kiểm tra POI thực tế dễ hơn.

## 10. AI/Vision và đánh giá submission

Backend đã có luồng đánh giá nhiệm vụ bằng AI/vision:

- Nhận submission ảnh từ người dùng.
- Lưu metadata ảnh, hash, vị trí và POI.
- Gửi submission vào pipeline đánh giá.
- Phân tích label/nội dung ảnh.
- Kiểm tra ảnh có khớp yêu cầu nhiệm vụ hay không.
- Kiểm tra điều kiện vị trí với nhiệm vụ có POI.
- Chuyển trạng thái submission sang approved hoặc rejected.
- Ghi thông tin AI metadata để phục vụ kiểm tra.
- Hỗ trợ manual/admin action cho submission.

Khi submission được duyệt, hệ thống cập nhật trạng thái quest, cấp XP và tạo notification tương ứng.

## 11. XP, cấp độ và lịch sử thưởng

Hệ thống gamification đã triển khai:

- Cấp XP khi hoàn thành quest.
- Cấp XP consolation khi quest bị từ chối trong một số trường hợp.
- Tránh cấp XP trùng cho cùng một submission.
- Lưu lịch sử XP transaction.
- Hiển thị XP gained toast trên mobile khi có notification thưởng.
- Hiển thị level và progress lên cấp trong profile.
- Màn hình XP History trong Settings.

XP notification được xử lý ở tầng global provider nên có thể hiện trên nhiều màn hình khác nhau, không phụ thuộc người dùng đang ở màn nào.

## 12. Huy hiệu và thành tựu

Hệ thống badge/achievement đã được triển khai:

- Danh sách huy hiệu.
- Chi tiết huy hiệu.
- Huy hiệu theo danh mục.
- Huy hiệu theo độ hiếm: common, rare, epic, legendary.
- Huy hiệu ẩn.
- Tiến độ mở khóa huy hiệu.
- Featured badges trên profile.
- Tự động đánh giá và award badge khi người dùng đạt điều kiện.
- Hiển thị badge mới mở khóa.
- Badge unlock celebration/toast toàn app.

Thông báo mở khóa thành tựu hiện được đưa lên global provider giống XP. Khi người dùng unlock badge ở bất kỳ flow nào, app có thể hiển thị celebration trên màn hiện tại. Ngoài notification `badge_unlocked`, app còn refresh nhẹ danh sách badge để phát hiện các thành tựu mới được award từ social action.

## 13. Notification

Hệ thống notification đã hỗ trợ:

- Lấy danh sách notification.
- Đếm notification chưa đọc.
- Đánh dấu một notification đã đọc.
- Đánh dấu tất cả đã đọc.
- Notification khi quest hoàn thành.
- Notification khi quest bị từ chối.
- Notification khi nhận like/comment/follow.
- Notification khi unlock badge.
- Đăng ký push token với Expo trong môi trường hỗ trợ.
- Poll notification trong app để hiển thị XP/badge toast kịp thời.

## 14. Recommendation và Explore

Hệ thống recommendation đã được triển khai để cá nhân hóa nội dung:

- Gợi ý quest dựa trên vị trí.
- Gợi ý quest theo sở thích người dùng.
- Gợi ý post trong feed.
- Ghi nhận event recommendation như shown, clicked, started, completed, ignored.
- Tính điểm recommendation dựa trên nhiều tín hiệu.
- Hỗ trợ các section như explore quests, trending near you, continue missions và explore new things.
- Tích hợp với Home/Explore trên mobile.

## 15. Admin Web

Trang admin web hỗ trợ quản trị hệ thống:

- Quản lý quest.
- Quản lý POI.
- Quản lý badge.
- Quản lý submission.
- Duyệt hoặc từ chối submission.
- Xem danh sách nội dung cần xử lý.
- Thao tác với bản đồ POI.
- Hiển thị vị trí hiện tại trong POI Manager.
- Build web admin thành công.

Admin có thể hỗ trợ kiểm duyệt, cấu hình dữ liệu nhiệm vụ, kiểm tra POI và quản lý các thành phần gamification.

## 16. Kiến trúc backend

Backend được tổ chức theo các lớp rõ ràng:

- API routes nhận request và trả response.
- Services xử lý nghiệp vụ.
- Repositories truy vấn database.
- Schemas định nghĩa request/response.
- Models định nghĩa bảng dữ liệu.
- Workers xử lý tác vụ nền như AI approval.
- Migrations quản lý thay đổi database.

Các nghiệp vụ quan trọng như quest, submission, XP, badge, notification, recommendation và POI đều được tách module riêng để dễ mở rộng.

## 17. Kiến trúc mobile

Mobile app được tổ chức theo Expo Router:

- Nhóm màn auth.
- Nhóm màn onboarding.
- Nhóm màn main.
- Modal post detail và quest detail.
- Context quản lý auth, user, post, toast, XP gain và badge.
- Service layer gọi API backend.
- Component tái sử dụng cho feed, quest, profile, badge, layout.

Ứng dụng có bottom navigation chính gồm Home, Quest, Camera, Notification và Profile.

## 18. Kiểm thử và kiểm tra chất lượng

Project đã có các kiểm tra và test ở nhiều phần:

- Backend có test cho quest flow, submission, admin, recommendation, social và AI approval.
- Đã bổ sung test cho việc phân biệt quest base và quest instance theo POI.
- Đã bổ sung test để Quest Log trả về completed POI instances.
- Mobile chạy lint bằng Expo lint.
- Web admin chạy build để kiểm tra khả năng compile.
- Backend chạy kiểm tra compile Python cho các file thay đổi.

## 19. Kết luận

Dự án LifeQuest đã hoàn thiện nhiều chức năng cốt lõi của một ứng dụng social gamification: đăng bài, làm nhiệm vụ, AI đánh giá ảnh, định vị POI, nhận XP, mở khóa thành tựu, cá nhân hóa feed và quản trị hệ thống. Điểm nổi bật của hệ thống là kết hợp nhiệm vụ thực tế theo vị trí với trải nghiệm mạng xã hội, giúp người dùng vừa tương tác cộng đồng vừa có động lực khám phá và hoàn thành thử thách.
