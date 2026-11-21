# Kế hoạch Phase 2 (TICKET-02 · Test Contract v1.1 · hạn tag `phase-2` 1:55)

- **Mục tiêu:** Nâng cấp toàn bộ số liệu chuẩn v1.1 (6 nguyên liệu, 6 món, 2 bếp, 4 bàn), hoàn thiện cá bơi/sinh, Cá Sấu Năm Chèo, vòng ngày `--mode day --days 1..5`, Shop nâng cấp (`oxygen`, `hp`), `pause`, Menu/HUD đầy đủ và kiểm chứng trước `1:55`.
- **Bước 0 (0–5 phút — khóa Contract v1.1 trên `main`):**
  - `tranha1764` + `hungdt31`: cập nhật `game.contract.json` (`contract_version: "1.1"`, số chuẩn, `day_plan` D1–D5, `shop`, `monsters`) và validator (`chonoi/contract.py`, `chonoi/inventory.py`, `chonoi/scenario.py`, `chonoi/inputs.py`).
- **Việc / người / phụ thuộc (5–35 phút):**
  - `tranha1764` (`feat/p2-gather-fish-swim`): nút `N5`/`N6` (`keo_neo`), bắt `ca_keo` (yield 2), cá bơi `1.5 m/s` phản xạ mép, đổi hướng mỗi `120` bước, sinh cá mỗi `360` tick (đầu ca 8, trần 12, `fish_spawned`). Phụ thuộc: Bước 0.
  - `ngthanhtamtb` (`feat/p2-gather-monsters`): Cá Sấu Năm Chèo (`M1` Ngày 1, `M2` Ngày 3), `patrol`/`chase`/`recoil`, mất Máu, rơi `floor(hold/2)` LIFO, `invuln_ticks: 90`, `monster_hit`, `faint(cause: "monster")`; cập nhật `docs/clarify.md`. Phụ thuộc: Bước 0.
  - `danhhieu204ns` (`feat/p2-quan-6dishes`): Quán 2 bếp (`B1`, `B2`), 4 bàn (`T1`–`T4`), 6 món; trong `day` lọc menu theo `day_plan[day].dishes` trước khi lọc nguyên liệu khả dụng; cập nhật `docs/retro.md`. Phụ thuộc: Bước 0.
  - `ngominhcuong` (`feat/p2-day-shop-pause`): `--mode day --days 1..5` (chuyển pha `day_start → day_plan → gather → quan → shop → days_complete`, `upgrades` → `active_upgrades` từ Ngày kế), Shop (`oxygen`/`hp`, `buy`/`shop_done`, `max_ticks: 600`), `pause`/`resumed` ở cả 3 mode. Phụ thuộc: Bước 0; tích hợp với `gather`/`quan`.
  - `nguyenquangtiep` (`feat/p2-ui-hud-menus`): Menu chính, `DayIntro`, `EveningIntro`, `DayResult`, `Summary`, Menu `Pause` (`Esc`/`P`), HUD sáng/tối mới (cảnh báo < 25%, `đã lấy/cần`, `"Thủy quái!"` + viền tím, `"Hết hơi!"`, Shop), chữ ≥ 18 px @ 1280×720. Phụ thuộc: snapshot `day`/`shop`/`monsters`.
  - `hungdt31` (`test/p2-qa-verification`): regression P1 theo số chuẩn v1.1, smoke tích hợp phút 20 (`docs/proof/phase-2/integration.*`), smoke `--mode day --days 1..5`, kiểm hiệu năng headless ≤ 20 s, `docs/verification/phase-2.md` & `docs/proof/phase-2/`. Phụ thuộc: Bước 0 + các nhánh lõi.
- **Rủi ro:**
  - Chế độ `day` phụ thuộc cả `gather` (cá/Cá Sấu/nâng cấp `oxygen`/`hp`) và `quan` (6 món/`day_plan`) → dùng fixture cố định để dựng `day` & `shop` song song từ phút 5.
  - Mở rộng (nhóm 6 người cần ≥ 2 mục cho cả buổi lab) chỉ làm sau khi lõi Phase 2 xanh trên `main`.
