# Nhật ký dùng AI (theo phase và theo người)

> Mỗi người ghi vào **mục của mình** (tránh conflict). Thêm dòng ở cuối bảng của mình.

## justapea25

| Phase | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|
| 1 | Claude Code (Claude Opus 5.5) | Code gather lát 1 (oxy, ngạt, Máu, ngất, `_add_to_hold`) + 9 test | chưa đo | Test reset bộ đếm ngạt bị đỏ: AI dựng scenario ở mặt nước với `zero_oxy_ticks > 0`, bị scenario từ chối (mã 2); sửa thành bắt đầu ngay dưới mặt nước rồi bơi lên. Tôi đọc lại luật và chạy toàn bộ test (41 OK) trước khi gộp |
| 1 | Claude Code (Claude Opus 5.5) | Dựng khung lát 2–4 (tách file, nối lời gọi), hợp đồng khách/sự kiện | chưa đo | Lần đầu AI ghi tên người vào docstring/TODO; tôi yêu cầu chỉ ghi theo lát |

## LETHESHIYING

| Phase | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|

## viethoang126

| Phase | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|

## minhthu27

| Phase | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|

## Kaylez-TXL

| Phase | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|

## linkiewinkie

| Phase | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|
| 1 | Codex | Bản nháp kế hoạch, TEAM, clarify, ma trận kiểm chứng và lệnh lưu bằng chứng | Chưa đo | Sửa cả file của người khác (dòng TEAM của 4 bạn, ma trận và bằng chứng của QA, standup). Tôi bỏ các phần đó khỏi nhánh và chuyển bản ma trận, bằng chứng cho QA. Trên Windows, lệnh đầu đọc stderr sai mã trang, phải bật UTF-8 cho tiến trình test. |
| 1 | Claude Code (Claude Opus 5.5) | Đối chiếu PRD-0 với contract, chốt clarify, AC-P1-xx trong plan, AGENTS.md, 2 skill, README, CREDITS | Chưa đo | Không đọc được PRD-0 trên lab board (mở theo giờ, cần đăng nhập) nên tôi dán PRD vào. AI phát hiện `events.md` và `customer.md` lệch tên trường so với PRD-0 mục D/E; tôi chốt theo PRD. |
