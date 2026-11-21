# 05: Mở rộng — Bảng xếp hạng cục bộ

**What to build:** Top 10 điểm lưu bền vững trên máy, mỗi lượt đủ 5 Ngày ghi đúng một mục, xuất được ra JSON để chứng minh.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] Khai `leaderboard` trong `extensions` của manifest.
- [ ] `<run_cmd> --export-leaderboard <out.json> [--leaderboard <store.json>]` xuất `{"entries":[{name,score,days_completed,seed}]}`, sắp điểm giảm dần, hòa thì mục ghi trước đứng trước (giữ thứ tự sau khi mở lại).
- [ ] Headless `day` nhận cặp `--leaderboard <store> --player-name <name>`; thiếu một cờ hoặc sai mode → mã 2.
- [ ] Chỉ ghi khi chạy **đủ 5 Ngày chuẩn**, **không scenario**, `reason: "days_complete"`; tối đa 10 mục; tên Unicode khác rỗng.
- [ ] File xếp hạng **không** làm đổi JSONL; soak **không** ghi xếp hạng.
- [ ] Test: ghi 2 lượt cùng seed → 2 mục, thứ tự đúng; mở lại store vẫn giữ thứ tự; lượt 4 Ngày không ghi.
