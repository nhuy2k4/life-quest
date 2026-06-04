# Plan: Event MVP V1 (Phase 1) + Chat 1-1 (Phase 2)

Muc tieu la chia 2 phase: Phase 1 hoan thanh Event MVP V1 (leaderboard, top 5, badge, notification, download anh) de demo trong 1 tuan; Phase 2 lam chat 1-1 (WebSocket, push, read status) trong 1 tuan tiep theo. Event tuan thuoc quest he thong, diem la like_count, moi user chi tinh post co like cao nhat, admin tao event, leaderboard polling 10-15s, end event snapshot va trao thuong/badge.

## Steps

1. Phase 1 — Data model event va quy tac ket thuc: bang `events`, `event_quests`, `event_results`; them `event_id` vao post; reward_config cho XP + badge; trang thai Draft/Active/Ended.
2. Phase 1 — Gan event vao post theo quest: khi post duoc tao tu quest thuoc event Active thi set `event_id`.
3. Phase 1 — Leaderboard: tinh diem theo like_count, moi user chi lay post co like cao nhat; top 5 + danh sach bai du thi; client polling 10-15s.
4. Phase 1 — Xoa post: event Active thi loai khoi leaderboard ngay; event Ended thi giu snapshot va hien "bai viet da bi xoa".
5. Phase 1 — End event: task hoac admin action set Ended, snapshot top 5 vao `event_results`, trao XP bonus + badge, gui notification.
6. Phase 1 — API/Service: CRUD event (admin only), list event, event detail + leaderboard, list posts theo event, end event, history.
7. Phase 1 — Mobile UI: Home feed hien event nhu quest dac biet, event detail (banner, time left, reward, top 5, danh sach bai), post detail tag event, nut luu anh ve may.
8. Phase 1 — Kiem thu: flow quest -> post -> event attach -> like -> leaderboard -> end -> reward; xoa post active/ended; download anh va xu ly quyen.
9. Phase 2 — Chat 1-1: model conversation/message/read; REST list/send/read; WebSocket realtime; push notification khi co tin moi; read status.
10. Phase 2 — Kiem thu chat: send/receive realtime, mark read, push khi app background.

## Relevant files

- be/app/api/v1/quests.py — submit quest va lien ket den flow tao post
- be/app/services/quest/quest_service.py — `submit_quest()` va logic xu ly submission
- be/app/workers/approval_tasks.py — xu ly approve/reject, noi can gan thong tin event khi tao post
- be/app/services/pipeline/approval_pipeline.py — pipeline duyet submission
- be/app/api/v1/social.py — tao post, like/unlike, feed
- be/app/services/social/social_service.py — `create_post()`, `like_post()`, `unlike_post()` cap nhat like_count
- be/app/models/social.py — Post/Like model, them `event_id`
- be/app/models/quest.py — Quest he thong
- be/app/models/submission.py — Submission tu quest
- be/app/models/user.py — role/permission admin
- be/app/services/notification/notification_service.py — gui push khi end event va chat
- be/app/models/notification.py — push token va in-app notification
- be/app/core/config.py — FCM/Expo config
- be/app/main.py — dang ky router va WebSocket
- mobile/app/(main)/home.tsx — hien event nhu quest dac biet
- mobile/app/post-detail.tsx — tag event + nut luu anh
- mobile/services/socialService.ts — goi API social/event
- mobile/services/notificationService.ts — push token

## Verification

1. Phase 1: tao event (admin) -> quest thuoc event -> submit/approve -> post gan event -> like -> leaderboard update theo polling.
2. Phase 1: xoa post active/ended dung quy tac; end event snapshot top 5, award XP + badge, gui notification.
3. Phase 1: mobile event detail render dung, polling 10-15s, download anh ok va xu ly tu choi quyen.
4. Phase 2: chat send/receive realtime, mark read, push notification khi app background.

## Decisions

- Chi admin duoc tao event.
- Diem event = like_count, moi user chi tinh post co like cao nhat.
- Leaderboard polling 10-15s, khong dung vote rieng.
- Event Ended giu snapshot; xoa post sau Ended khong doi ket qua.
- Badge tai dung bang `badges` hien co.

## Further considerations

1. Quy tac chat: follower 1 chieu hay 2 chieu moi duoc chat.
2. Co can auto-activate event theo `start_at` hay chi admin bat/tat.
3. Co can cache leaderboard hay denormalize de giam tai khi polling nhieu.
