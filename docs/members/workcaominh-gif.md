# workcaominh-gif — Cao Duy Minh (Integrator, `sim/gather`)

> Bản nháp do AI (Claude Code) soạn theo yêu cầu của mình từ lịch sử repo; mình đã đọc lại và chịu trách nhiệm nội dung (ghi trong `docs/ai-usage-log.md`).

## Phần mình làm
- Integrator: fork, ghép code các lát, gắn tag `phase-1`–`phase-4`, phát hành Release v1.0.0.
- Điều phối agent làm luật `sim/gather` + `sim/quan` (P1–P3), bench/soak (P4) và bản GUI: lặn, quán nhà bè, vòng Ngày, chợ, âm thanh, ảnh/video demo.

## Đã giúp ai
- Gộp commit của Duyet và Nhật Minh vào `main`, chạy lại test trước khi push.
- README 3 lệnh và `tools/package.sh` cho cả nhóm.

## AI sai ở đâu
- Agent tự commit khi chỉ được sửa file → gỡ bằng `git reset --soft`.
- Client sập khi `fish_initial` đổi từ mảng sang số; agent báo "xong" chỉ dựa test headless → chơi thử trên trình duyệt mới thấy lỗi ("Bưng undefined", kẹt món, "Giỏ 0/10").
- Một commit bị sửa tác giả sang tên người khác trên máy → kiểm `git log`, dựng lại lịch sử đúng tên trước khi push.

## Bài học
"Xong" = test xanh + chơi thử thật. Kiểm tác giả trước mỗi lần push. Gắn tag đúng giờ (`phase-2` trễ 4 phút).

## Commit & bằng chứng
`37f371d` · `4951d27` · `ae814d2` · `1a9bf8d` (tag/Release) · `18849de` (media). 25 commit `cduyminh`; 18 commit `hxlinh` (Phase 1–2) tạo từ máy mình.
