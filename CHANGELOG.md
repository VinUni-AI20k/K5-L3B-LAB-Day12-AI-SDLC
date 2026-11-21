# Changelog

Mỗi phase một mục; mới nhất ở trên. Mã phiên bản hợp đồng nằm trong `game.contract.json` (`contract_version`).

## [Chưa phát hành] Mở rộng Phase 4 (TICKET-04 mục 3)
### Thêm
- Bảng xếp hạng cục bộ: `chonoi/leaderboard.py` (top 10, điểm giảm dần, hòa giữ thứ tự ghi, ghi nguyên tử).
  Headless `--mode day` nhận cặp `--leaderboard <store> --player-name <name>`; ghi một mục khi đủ 5 Ngày chuẩn.
  `<run_cmd> --export-leaderboard <out> [--leaderboard <store>]` (`chonoi.live`). JSONL không đổi.
- Bản GUI: nhập tên + bảng top 10 sau màn tổng kết 5 Ngày (`client/src/leaderboard.js`, localStorage `chonoi.lb`).
- Phụ đề SFX ở bản GUI (`client/src/captions.js`): phím **U**, mục trong menu tạm dừng, tự bật khi tắt tiếng;
  phụ đề riêng cho ba cảnh báo (Cá Sấu gần, oxy sắp hết, khách sắp giận) và các lần bị thương.
- `tests/test_leaderboard_p4.py` (17 test); bằng chứng `docs/proof/phase-4/ext/`.
### Lưu ý khung
- Sửa `chonoi/live.py` (khung giảng viên): `--mode` không còn bắt buộc khi chỉ `--export-leaderboard`, vì `run_cmd` trỏ vào đây.

## [v1.0.0] Phase 4 — Release (Test Contract v1.3, TICKET-04)
### Hợp đồng
- `contract_version` 1.3; thêm khóa gốc `bench_cmd` (`python3 tools/bench.py`) và `soak_cmd` (`python3 tools/soak.py`).
  Từ 1.3, `load_contract` từ chối hợp đồng thiếu hoặc để rỗng hai khóa này (mã 2).
- Không đổi schema kho, scenario hay event so với v1.2; regression P1–P3 giữ nguyên.
### Thêm
- `tools/soak.py`: một tiến trình chạy N Ngày liên tiếp (Ngày > 5 lặp kế hoạch D1–D5 theo `((day-1) % 5) + 1`),
  ghi `{"days","days_completed","crashes","results","duration_s"}`; đạt khi `crashes == 0`.
- `tools/bench.py`: đo FPS bản GUI bằng Chrome/Chromium headless 1280×720, ghi `{avg_fps,p1_low_fps,frames,measured_s,load_ms}` (lệnh `bench_cmd`).
- `tools/package.sh`: tạo `dist/quan-an-cho-noi-v1.0.0.zip` kèm `run.sh` / `run.command` (mở server + trình duyệt).
- Bản GUI: chế độ tương phản cao (phím **H**, lưu trong trình duyệt), địa hình đáy sông và dòng nước lũ,
  bảng thực đơn chọn món + số suất, Chợ Chú Sáu mua/bán, video mở đầu, ảnh bìa của nhóm.
- Tài liệu phát hành: `LICENSE` (MIT cho mã, asset giữ giấy phép riêng), `CREDITS.md` cập nhật,
  `docs/release/RELEASE_NOTES_v1.0.0.md`, retro Phase 4, khung phản tư `docs/members/<handle>.md`.
### Sửa
- `.gitignore` bỏ qua `dist/`.

## [Phase 3] Contract v1.2 — Độ tươi (TICKET-03)
### Breaking
- `contract_version` 1.2, thêm `tuning.freshness {initial,gather_decay_per_s,quan_decay_per_s,spoiled_below}` = 100, 0.5, 0.25, 30.
- File kho: `{"items":{kind:n}}` → `{"items":[{"id","kind","fresh"}]}` (sắp theo id). Quán v1.2 trả mã 2 cho file kho đếm.
- Scenario: `gather.hold`, `quan.stock` là mảng cá thể; `customers[].reserved` là mảng id cá thể.
- Snapshot `hold`/`stock` (quán, Shop)/`customers[].reserved` theo schema mới; `cook_started.data.items` là mảng cá thể (kind rồi id).
- `base_price` chốt lúc bắt đầu nấu = floor(giá niêm yết × mean fresh / 100); boa tính trên giá chốt.
### Thêm
- Event `spoiled {item_id,kind,location}`; hao tươi kho quán 1 đơn vị/tick (240 đơn vị/điểm), pause dừng hao, Shop không hao.
### Cập nhật fixture
- Kho đếm `{"ca_loc":2}` → `[{"id":"S1","kind":"ca_loc","fresh":100},{"id":"S2",...}]`; `reserved {"ca_loc":1}` → `["S1"]`.
- Regression P1–P2 đi qua `tests/v12_compat.py` (lý do trong docstring); giá kỳ vọng 60→59, 200→199 vì luật giá theo fresh.

## [Phase 2] Contract v1.1 — Vòng Ngày (TICKET-02)
### Breaking
- Số chuẩn mới: 4 bàn, 2 bếp, 6 nguyên liệu, 6 món; `fish_initial` đổi từ danh sách đàn cố định sang **một số** (8 đàn sinh theo seed, cá bơi).
- Nút `attack` hợp lệ; thêm `--mode day --days N` (1..5).
### Thêm
- Vòng Ngày gather → quán → Shop trong một tiến trình; kho bàn giao trong bộ nhớ; `day_plan` D1–D5 của Má Tư lọc thực đơn.
- Cá Sấu Năm Chèo, Máu / ngất, nâng cấp `oxygen` / `hp` mua ở Shop (hiệu lực từ Ngày kế), `pause` ở cả ba pha.
- Bản GUI `client/`: vòng Ngày, lặn bằng lao móc, quán nhà bè đêm, nhạc tổng hợp.
### Cập nhật test
- 4 test P1 sửa kèm lý do (xem `docs/verification/phase-2.md`).

## [Phase 1] Contract v1.0 — PRD-0
### Thêm
- Sim headless `gather` (bơi, oxy, ngạt, hái, bắt cá, cập bến) và `quan` (khách, giữ chỗ, bếp, phục vụ, boa, uy tín).
- Hợp đồng file kho `{"items":{kind:n}}` nối hai buổi; `python3 -m chonoi.headless --mode gather|quan`.
- Cửa sổ chơi thử `python3 -m chonoi.live`.
