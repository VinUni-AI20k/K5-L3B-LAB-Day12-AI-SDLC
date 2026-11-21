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
| 1 | Claude Code (Claude Sonnet 5.5) | Đọc repo, phân tích phần việc; code gather lát 2 (`try_gather`, `try_catch`) + 16 test hộp đen | chưa đo | 2 test đầu bị đỏ do AI viết sai test, không phải sai luật: (1) scenario đặt cá ở mặt nước bị headless từ chối (mã 2, cá phải ở dưới nước); (2) test hồi chiêu lệch 1 tick vì bấm hai lần liên tiếp không có frame thả nút nên không có cạnh lên. Tôi đọc lỗi, sửa test, chạy lại toàn bộ (57 OK) trước khi đẩy |
| 1 | Claude Code (Claude Sonnet 5.5) | Soạn giả định gửi PO, điền TEAM/members/nhật ký | chưa đo | AI đưa tên hiển thị tạm là handle vì không biết họ tên thật; tôi cần tự thay |

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
