# Kế hoạch Phase 2 (≤ 1 trang)

- **Mục tiêu:** Nâng cấp game lên **Test Contract v1.1** trong 55 phút (`1:00–1:55`): 6 nguyên liệu, 6 món, pause, `--mode day` (vòng ngày D1–D5 + Shop nâng cấp), cá bơi/sinh (8→12 đàn, nút N5/N6), Cá Sấu + mở rộng Rắn Hổ Mây (`snake`), 2 bếp 4 bàn (+ dự phòng Cháy món `burn`), UI vòng ngày đầy đủ (Menu, DayIntro, EveningIntro, DayResult, Shop, Summary, Pause, HUD v1.1 sans-serif ≥ 18 px, ≥ 30 FPS), smoke tích hợp & regression P1, retro và gắn tag `phase-2` trước 1:55.

- **Bảng đầu việc theo AC:**

| Mã AC | Nội dung chính | Phụ trách | Phụ thuộc |
|---|---|---|---|
| `AC-P2-01` | Nền Contract v1.1 (`game.contract.json`, `contract.py`, `inventory.py`, `scenario.py`, `inputs.py`, `headless.py`, `PauseGate` trong `runner.py`, `docs/contracts/README.md`) | `LeBao403` | — |
| `AC-P2-02` | Cá Sấu (`patrol`/`chase`/`recoil`, `monster_hit`, mất `floor(len*0.5)` LIFO, bất tử 90 tick, ngất `cause:"monster"`, M2 từ Ngày 3) | `LeBao403` | `AC-P2-01` |
| `AC-P2-03` | Mở rộng Rắn Hổ Mây (`species.ran`, `M3`, `"extensions": ["snake"]`, test riêng & ghi README) | `LeBao403` | `AC-P2-02` |
| `AC-P2-04` | Nút N5/N6 (`keo_neo`), cá kèo (`ca_keo`, yield 2), 8 đàn đầu ca (`fish_init`) | `LaanLee` | `AC-P2-01` |
| `AC-P2-05` | Cá bơi (`fish_speed`, dải `fish_depths`, đổi hướng `fish_turn` mỗi 120 tick, phản xạ mép) & sinh cá (`fish_spawn` mỗi 360 tick, tối đa 12, `fish_spawned`) | `LaanLee` | `AC-P2-04` |
| `AC-P2-06` | 2 bếp (`B1`, `B2`), 4 bàn (`T1`–`T4`), 6 món đọc động từ `menu`, ưu tiên tương tác gần nhất | `baoduy2048` | `AC-P2-01` |
| `AC-P2-07` | Mở rộng dự phòng Cháy món (`burn_s: 20`, `dish_burnt`, giữ lại nguyên liệu hoặc `unfulfillable`) | `baoduy2048` | `AC-P2-06` |
| `AC-P2-08` | Vòng ngày `--mode day` (`chonoi/day.py` `DaySession`: `day_start`, `day_plan` D1–D5, `gather`→`quan`→`shop`, mang tiền/uy tín/nâng cấp qua Ngày, lọc món theo kế hoạch, < 20s/Ngày) | `TheDLCrimson` | `AC-P2-01` |
| `AC-P2-09` | Shop & nâng cấp (`chonoi/shop.py` `ShopSim`: `buy` `oxygen`/`hp`, `bought`/`buy_failed`, `shop_done`/`shop_end` 600 tick, áp cấp mới từ Ngày kế, kiểm scenario `day`) | `TheDLCrimson` | `AC-P2-08` |
| `AC-P2-10` | Nối `chonoi/live.py --mode day` (`DaySession`, nhận `pause`, `shop_done`, `buy`, giữ nguyên API cũ) | `common-maker` | `AC-P2-08`, `AC-P2-09` |
| `AC-P2-11` | Màn hình vòng ngày & Pause trên `chonoi/web/index.html` (Menu, DayIntro 4s, EveningIntro, DayResult, Shop, Summary Ngày 5, Pause `Esc`/`P` dừng sim thật) | `common-maker` | Dữ liệu giả; nối `AC-P2-10` |
| `AC-P2-12` | HUD v1.1 (sans-serif ≥ 18 px ở 1280×720, ≥ 30 FPS; sáng: 6 loại, `đã lấy/cần`, đổi màu ≤ 30s, gợi ý hái/bến, `"Thủy quái!"` viền tím, `"Hết hơi!"`; tối: 2 bếp, 4 bàn, 6 món, kho khả dụng, kiên nhẫn < 25%) | `common-maker` | `AC-P2-01` |
| `AC-P2-13` | Smoke tích hợp (`docs/proof/phase-2/integration.txt`), smoke `--mode day --days 1` & `--days 2` có `buy`, regression toàn bộ `tests/` (chỉnh có điều kiện `test_smoke_p1.py`), skill `smoke-day` | `common-maker` | `AC-P2-01`..`12` |
| `AC-P2-14` | DoD Phase 2: `docs/verification/phase-2.md`, `docs/proof/phase-2/`, `docs/retro.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `TEAM.md` 5 người pass `check_team.py`, tag `phase-2` trên `main` trước 1:55 | `common-maker` & cả nhóm | `AC-P2-01`..`13` |

- **Mốc phối hợp (55 phút):** `1:00–1:05` kế hoạch + việc tồn P1 (`TEAM.md`, tag `phase-1`); `1:15` nền v1.1 đã lên `main`, cả nhóm pull; `1:20` smoke tích hợp `gather`→`quan`, standup & điều người hỗ trợ; `1:35` đóng băng tính năng, smoke `day` & regression P1; `1:45` retro; `1:50–1:55` dự phòng & `LeBao403` đẩy tag `phase-2`.

- **Rủi ro & giảm thiểu:**
  - *Việc tồn P1:* `TEAM.md` hiện chưa điền (`check_team.py` báo lỗi) và chưa có tag `phase-1` → nhắc nhóm chốt ngay đầu Phase 2.
  - *Đổi font sans-serif ≥ 18 px ở 1280×720:* bố trí lại kích thước hộp HUD v1.1 trong `chonoi/web/index.html` để chữ to, rõ mà không tràn/che khu vực chơi và giữ ≥ 30 FPS.
  - *Conflict `gather.py` / `quan.py`:* giữ nguyên thứ tự hàm trong `step()`, chỉ sửa thân hàm thuộc lát của mình.
