# Kế hoạch Phase 2 (≤ 1 trang)

- **Mục tiêu:** Test Contract v1.1 (TICKET-02, [`docs/contracts/ticket-02-test-contract-v1.1.md`](../contracts/ticket-02-test-contract-v1.1.md)):
  số chuẩn + dữ liệu 6 món / kế hoạch D1–D5 / Shop trong `game.contract.json`, cá bơi/sinh, Cá Sấu + Máu/ngất,
  2 bếp / 4 bàn, `--mode day` (vòng Ngày, Shop, nâng cấp), pause cả ba mode, smoke tích hợp, tag `phase-2` trước 1:55.

## Lát / người / phụ thuộc (khớp `TEAM.md`, theo gợi ý mục 5 của ticket)

| Mã AC | Lát | Người (agent hỗ trợ) | File chính | Phụ thuộc |
|---|---|---|---|---|
| AC-P2-01..02 | Số chuẩn + dữ liệu v1.1 (`contract_version` 1.1, 6 món, B1/B2, T1–T4, day_plan, shop, monsters, khóa cá) | Minh (agent A) | `game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py` | — (làm đầu tiên, các lát khác đọc) |
| AC-P2-03..15 | (1) Cá bơi / sinh theo seed, cá kèo, nút kèo nèo | Minh (agent A) | `chonoi/sim/gather.py`, `tests/test_gather_p2.py` | AC-P2-01 |
| AC-P2-16..29 | (2) Cá Sấu, Máu, bất tử, ngất, bố trí theo Ngày, tham số nâng cấp | Minh (agent A) | `chonoi/sim/gather.py`, `tests/test_gather_p2.py` | AC-P2-01 |
| AC-P2-30..35 | (3) Quán 2 bếp / 4 bàn / 6 món, lọc thực đơn theo kế hoạch Ngày | Duyet (agent B) | `chonoi/sim/quan.py`, `tests/test_quan_p2.py` | AC-P2-01 |
| AC-P2-40..42 | (4a) Pause ba mode ở lớp runner | Nhat Minh (agent B) | `chonoi/runner.py`, `chonoi/inputs.py` | — |
| AC-P2-50..54, 60..65, 70..72 | (4b) Vòng Ngày, Shop, nâng cấp, scenario `day`, CLI `--days` | Nhat Minh + Duyet (agent B) | `chonoi/sim/day.py`, `chonoi/sim/shop.py`, `chonoi/scenario.py`, `chonoi/headless.py`, `tests/test_day_p2.py` | lát 1–3 (API `GatherSim(day, oxygen_max_s, hp_max)`) |
| AC-P2-80, 90..91 | Hiệu năng, smoke tích hợp, bằng chứng, ma trận | Nhat Minh (QA) | `tests/test_smoke_p2.py`, `docs/proof/phase-2/`, `docs/verification/phase-2.md` | tất cả |
| UI | Menu, DayIntro/EveningIntro/DayResult/Summary, HUD, pause menu | Nhat Minh | `client/`, `chonoi/live.py` | snapshot v1.1 |
| Tag | Chạy lại test + proof ở commit tag, gắn `phase-2` | Minh (Integrator) | — | tất cả |

**Giao diện chuyển pha đã chốt (fixture để tích hợp sớm):** `GatherSim(tuning, scenario, streams, ids, day, oxygen_max_s, hp_max)`;
bàn giao `sim.inventory_items()` (schema kho đếm, `{}` sau ngất) → `QuanSim(..., inventory=, menu_filter=, reputation=, money=, earned=)`
→ `ShopSim(tuning, money, upgrades, stock)`. Pause không đụng vào sim: runner không gọi `step()`.

## Rủi ro
- Lệch tick ở chỗ đổi pha (cùng tick, pha mới chạy từ bước sau) → test AC-P2-51 khóa đúng tick + `phase_tick:0`.
- Test P1 vỡ vì số chuẩn (4 bàn, 8 đàn, nút `attack` hợp lệ) → sửa test kèm lý do trong docstring, không sửa luật cho xanh.
- UI (menu/HUD/pause trong trình duyệt) chưa xong → ghi "chưa đạt" trung thực trong ma trận.
