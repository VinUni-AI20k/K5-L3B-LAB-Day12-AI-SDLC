# Nhật ký dùng AI (theo phase và theo người)

> Mỗi người **chỉ ghi vào mục của mình** (tránh conflict khi merge). Thêm dòng mới ở cuối bảng của mình.

## A — `sim/gather` + PO

| Phase | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|


## B — `sim/quan` + Scrum

| Phase | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|
| 1 | Claude Code (Sonnet 4.6) | Hoàn thiện `sim/quan.py` phần 3+4: khách, bếp, bàn, tiền, uy tín | ~15k tokens | Ban đầu dùng `inp.interact` thay vì `inp.pressed("interact")` — fix ngay sau khi chạy test. Snap đúng 32/32. |


## C — `client/ui` + Integrator

| Phase | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|
| 1 | Claude Code (Opus 5.5) | Đọc repo, chia việc 4 người, soạn hợp đồng `docs/contracts/README.md` | | Bản đầu đoán `data` sự kiện khi chưa có PRD-0 (sai vài chỗ: `amount` thay vì `count`, thiếu `required/free` ở `hold_full`, bắt cá thiếu chỗ không đặt hồi chiêu). Sửa lại sau khi dán PRD-0. |
| 1 | Claude Code (Opus 5.5) | Viết kiểm mâu thuẫn scenario quán (`scenario.py`), HUD quán (`index.html`), README, TEAM.md | | Kiểm bằng 32 test + 12 ca scenario tay (đúng mã 0/2). Giả định chưa rõ ghi `docs/clarify.md` #1–5. |


## D — `qa` + harness

| Phase | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|
