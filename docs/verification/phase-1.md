# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| Khai báo nhóm & contract (`TEAM.md`, `game.contract.json`) | Chạy `python3 tools/check_team.py` | [TEAM.md](../../TEAM.md), [game.contract.json](../../game.contract.json) | Đạt (`OK: 6 thành viên`) |
| Bộ test tự động nền tảng (`tests/`: unit, live, smoke P1, team check) | Chạy `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` | [unittest.log](../proof/phase-1/unittest.log) | Đạt (32/32 tests OK) |
| Headless smoke mode `gather` (seed 1, 600 ticks) | Chạy `python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out docs/proof/phase-1/smoke-gather.jsonl` | [smoke-gather.jsonl](../proof/phase-1/smoke-gather.jsonl) | Đạt (`reason: tick_limit`) |
| Headless smoke mode `quan` (seed 1, 600 ticks) | Chạy `python3 -m chonoi.headless --mode quan --seed 1 --ticks 600 --out docs/proof/phase-1/smoke-quan.jsonl` | [smoke-quan.jsonl](../proof/phase-1/smoke-quan.jsonl) | Đạt (`reason: tick_limit`) |
| Smoke 2 tiến trình nối kho (`gather --inventory-out` → `quan --inventory`, Mục G) | Chạy `gather` (seed 42, `dock.json`, `dock-inputs.json`, `--ticks 1`) xuất `handoff-catch.json`, rồi `quan --inventory handoff-catch.json --ticks 0` | [handoff-catch.json](../proof/phase-1/handoff-catch.json), [handoff-gather.jsonl](../proof/phase-1/handoff-gather.jsonl), [handoff-quan.jsonl](../proof/phase-1/handoff-quan.jsonl) | Đạt (`stock` tick 0 khớp `{"bong_sung":2,"ca_loc":1}`) |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt:
  - Đạt: Toàn bộ 32 test nền tảng, kiểm tra cấu hình nhóm (`check_team.py`), và smoke headless 2 tiến trình (`gather`, `quan`) đều chạy thông suốt.
  - Chưa đạt / đang chờ: Các AC nghiệp vụ bổ sung của Phase 1 (từ PR của `sim/gather`, `sim/quan`, `client/ui`) sẽ được cập nhật thêm vào bảng khi các lát hoàn thành.
- Điều cần chỉnh cho phase sau:
  - Bổ sung test case mới vào `tests/` ngay khi có PR từ các lát và lưu log đối chiếu theo từng PR.
