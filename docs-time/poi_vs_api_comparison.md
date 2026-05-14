# POI (Local DB) vs. Call API Trực Tiếp — So sánh và Khuyến nghị

## Tóm tắt

Tài liệu này so sánh hai cách lấy/validate vị trí/POI khi người dùng nộp ảnh cho quest:

- POI local: duy trì cơ sở dữ liệu POI (ingest, cache, matcher) và match offline.
- Call API trực tiếp: gọi provider bên ngoài (Overpass, Google Places, v.v.) tại thời điểm xử lý.

Mục tiêu: giúp team chọn chiến lược phù hợp cho throughput, độ tin cậy, chi phí và khả năng vận hành.

---

## Ưu / Nhược — POI local (DB + matcher)

Ưu điểm

- Truy xuất nhanh, latency thấp (không round‑trip network cho mỗi submission).
- Ổn định, không phụ thuộc 3rd‑party runtime; phù hợp với scale lớn.
- Dễ tối ưu (index, bbox, precompute radius) và cache kết quả.
- Chi phí thấp hơn khi volume cao (không trả theo request).
- Deterministic & audit‑friendly (cùng input → cùng kết quả), dễ debug.
- Cho phép mở rộng dữ liệu custom (labels mapping, template mapping, source attribution).

Nhược điểm

- Cần vận hành: ingest pipeline (OSM, nguồn thương mại), UPSERT, migration, cleaning.
- Dữ liệu có thể stale nếu không sync đủ thường xuyên.
- Ban đầu có chi phí lưu trữ và chỉ mục.
- Phủ sóng có thể hạn chế ở vùng mới nếu nguồn dữ liệu kém.

---

## Ưu / Nhược — Call API trực tiếp (On‑demand)

Ưu điểm

- Dữ liệu luôn tươi (do provider duy trì); ít cần ingest nội bộ.
- Phủ sóng rộng và nhiều thông tin phong phú (rating, address, metadata).
- Ít vận hành nội bộ (không cần DB ingest pipeline).

Nhược điểm

- Latency cao hơn, phụ thuộc mạng và provider speed.
- Có rate limits và chi phí theo request (không phù hợp volume lớn).
- Kết quả không deterministic (provider thay đổi data bất ngờ).
- Cần bình thường hóa response cho rule engine và audit.

---

## Khuyến nghị chiến lược (practical)

1. Primary: **POI local + cache** — dùng làm luồng chính nếu bạn cần throughput cao, low latency, auditability, và custom rules.
2. Fallback: **Call external API** khi local POI không trả kết quả (vùng chưa có dữ liệu) hoặc để enrich metadata.
3. Sync cadence: ingest OSM (Overpass) hàng tuần hoặc theo vùng thay đổi; cho các khu vực trọng yếu (thành phố) ingest hàng ngày.
4. Thiết kế hybrid: lưu `source` + `external_id` cho mỗi POI và giữ `is_active` flag; chỉ update via controlled ingest.

---

## Vận hành & kỹ thuật (gợi ý thực thi)

- Index: b-tree trên `latitude`, `longitude` kết hợp GiST/BRIN nếu cần; unique index trên `(source, external_id)` để UPSERT.
- Cache: Redis TTL (ví dụ 10–600s, tuỳ use case) cho match results; key dạng `poi:suggest:{lat_round}:{lng_round}`.
- Matching: bbox prefilter (max radius), tính Haversine để xác định distance, chọn POI gần nhất trong radius.
- Ingest: batch UPSERT với `ON CONFLICT` để tránh N+1; log counts (insert/update) để audit.
- Monitoring: expose metrics — match latency, cache hit ratio, fallback to external API rate, rejected submissions due to `poi_required` missing.

---

## Khi nên dùng API trực tiếp ngay (use cases)

- POC / dev nhanh không muốn ingest dữ liệu.
- Vùng có ít traffic và bạn chấp nhận latency/chi phí.
- Khi cần metadata phong phú mà local DB chưa lưu (ví dụ reviews, opening hours) và chỉ dùng cho hiển thị, không cho rules realtime.

---

## Ví dụ flow đề xuất (hybrid)

1. Submission arrives with `lat/lng`.
2. Try `match_poi(lat,lng)` against local DB (fast). If matched: use `poi_id` and continue.
3. If not matched and fallback enabled: call external API (e.g., Overpass/Places) to search nearby; if found, optionally ingest the POI (or cache result) and continue.
4. Store `poi_source` (`local` or provider name), `external_id` if any, and `poi_distance_m` for rule engine.

---

## Metrics / KPIs để theo dõi

- Cache hit ratio (Redis) cho POI match.
- % submissions that require fallback to external API.
- Average match latency (local vs external).
- Volume of POI upserts per ingest job.
- Rejection rate due to `poi_required` missing.

---

## Tham chiếu code trong repo

- POI matcher: `app/services/poi/poi_matcher.py`
- Repositories/ingest: `be/scripts/osm_ingest.py` và `app/repositories/poi_repository.py`
- Approval pipeline: `app/workers/approval_tasks.py` và `app/services/ai/ai_approval_service.py`

---

## Kết luận ngắn

- Nếu hệ cần scale, latency thấp và auditability: chọn **POI local + cache**.
- Dùng external API làm **fallback/enrichment** cho vùng thiếu dữ liệu.

_File auto‑generated._
