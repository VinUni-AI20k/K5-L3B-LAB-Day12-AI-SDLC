# Kế hoạch Phase 2 — Ticket-02 "Một ngày ở chợ nổi" (1:00–1:55)

Yêu cầu: [`docs/prd/phase-2.md`](../prd/phase-2.md) · Test Contract v1.1 · hạn tag `phase-2` 1:55.

## 0. Hiện trạng khi vào Phase 2 (ghi trung thực)
- Xong: lát 1 (oxy, ngạt, Máu, ngất — `_update_oxygen`, 13 test), khung hàm theo lát, 2 skill.
- **Nợ Phase 1:** lát 2 (`_try_gather`, `_try_catch`), lát 3 + lát 4 (toàn bộ quán) còn TODO. Test ẩn chấm lại P1, nên **trả nợ P1 nằm trong lát Phase 2 tương ứng**, làm trước phần mới.
- Chưa có tag `phase-1` → gắn ngay trên `main` hiện tại, ghi phần chưa đạt trong `docs/verification/phase-1.md`.
- `_add_to_hold` (không đủ chỗ thì không thêm gì) **khớp** PRD ("cần đủ chỗ cho cả đàn", "thiếu chỗ phát hold_full, nút giữ nguyên").

## 1. Lát 0 — Nền v1.1 (Integrator, phút 0–15, CHẶN mọi lát khác → làm trước, merge sớm)
Đụng khung giảng viên nên một người làm, báo cả nhóm:
- `game.contract.json`: `contract_version: "1.1"`, số chuẩn mục 1.1–1.3 + khóa mục 4.1 (fish_* , N5/N6, `fish_initial` 8 đàn, `monsters`, B2, T2–T4, 6 món, `day_plan`, `shop`), sửa `team_size`.
- `chonoi/contract.py`: bỏ ràng buộc v1.0 (đúng 6 đàn, chỉ 2 loại nút/2 loài cá), kiểm khóa mới.
- `chonoi/inventory.py`: thêm `ca_keo`, `keo_neo` vào danh sách kind.
- `chonoi/scenario.py`: khóa mới (`monsters`, `fish[].age_ticks`, `random_customers`, khối `day`), kind mới.
- `chonoi/inputs.py`: nút `pause`, `shop_done`, chuỗi `buy` (attack/photo chỉ khi bật mở rộng).
- Test cũ phải đổi vì luật mới (ghi lý do trong commit): `test_con_03_old_and_future_modes_rejected` (`day` giờ hợp lệ), `test_gather_snapshot_has_gather_fields` (6 → 8 đàn).
- Xong thì chạy toàn bộ test, cập nhật `docs/contracts/README.md` (sự kiện v1.1, cấu trúc khách, giao diện day ↔ gather/quan).

## 2. Các lát song song (sau khi lát 0 merge; trong lúc chờ: viết test hộp đen trước)
| Lát | Người | Phạm vi (AC) | File / hàm sở hữu |
|---|---|---|---|
| 2 | B | **Nợ P1:** hái, bắt cá (AC-P2-01). **Mới:** cá bơi 1.5 m/s, đổi hướng mỗi 120 bước theo seed, phản xạ mép; sinh cá mỗi 360 tick, trần 12, trọng số loài (AC-P2-02); sự kiện `fish_spawned` | `gather.py`: `_try_gather`, `_try_catch`, `_move_fish` (mới), `_spawn_fish` (mới) |
| 1 | A (s0ra1n0, Integrator) | Sau lát 0: Cá Sấu M1/M2 — patrol/chase/recoil, hit (−1 Máu, bỏ floor(n/2) LIFO, bất tử 90), faint `cause:"monster"` (AC-P2-03) | `gather.py`: `_update_monsters` (mới), tách `_faint(cause, events)` dùng chung với `_update_oxygen` |
| 3 | C (PO) | **Nợ P1:** khách theo lịch, giữ chỗ, kiên nhẫn, `customer_left`, `no_dish`, dựng khách từ scenario (AC-P2-04). **Mới:** 4 bàn, lọc món theo `allowed_dishes` (kế hoạch ngày) | `quan.py`: `_tick_customers`, `_spawn_customers`; nhận tham số `allowed_dishes=None` |
| 4 | D | **Nợ P1:** bếp, bưng, phục vụ, `paid`, boa, uy tín, đóng ca (AC-P2-05). **Mới:** 2 bếp, 6 món (dữ liệu sẵn); kiểm mâu thuẫn scenario quán | `quan.py`: `_tick_stoves_and_eating`, `_interact`, `_close_shift`; `scenario.py`: `_validate_quan` |
| 5 | E (QA lead) | `--mode day` + `--days`: vòng DayIntro → gather → quan → Shop, `day_start`/`day_plan`/`phase_start`, bàn giao kho trong bộ nhớ, Shop (`bought`, `buy_failed`, `shop_end`, 600 tick), áp cấp oxygen/hp từ Ngày kế (AC-P2-06); pause ở cả 3 mode (AC-P2-07) | `chonoi/sim/day.py` (mới), `chonoi/sim/shop.py` (mới); `headless.py`/`runner.py` (khung — báo nhóm): mode day, `sim_tick` ≠ `tick` khi pause, dòng end `days_completed` |

Người xong sớm (rà ở phút 20): HUD/menu theo mục 2 "Menu, pause và HUD" trong `chonoi/web/index.html` + `chonoi/live.py` (AC-P2-08).
Mở rộng (nhóm 5 người cần ≥ 1 mục, cả buổi lab): đề xuất **burn** (`burn_s: 20`, nhỏ, nằm trong lát 4) — chỉ làm khi lõi xanh; khai trong `extensions` + README.

## 3. Giao diện cần chốt ngay phút 0–5 (ghi `docs/contracts/README.md`)
- `GatherSim(tuning, scenario, streams, ids, day=1, upgrades=None)` → `oxygen_max`, `hp_max` theo cấp đang áp dụng; bố trí Cá Sấu theo `day`.
- `QuanSim(..., inventory, allowed_dishes=None, carry=None)` → `carry` = money/earned/reputation xuyên Ngày.
- Mỗi sim có `done`, `reason`, `inventory_items()`, `snapshot()`, `step(inp)`; `day.py` chỉ gọi các hàm này, không đọc trạng thái bên trong.
- Event trong day có thêm `day`; event kết thúc mang pha cũ; snapshot đổi pha có `phase_tick: 0`.

## 4. Mốc thời gian
| Phút | Việc |
|---|---|
| 0–5 | Đọc ticket, chốt giao diện mục 3, chia người. A bắt đầu lát 0; người khác viết test hộp đen của lát mình |
| 5–20 | Lát 0 merge (chậm nhất phút 15). Các lát code + test |
| 20 | Smoke tích hợp gather `--inventory-out` → quan `--inventory`, lưu `docs/proof/phase-2/integration.*`. Standup 2–3 phút, điều người sang lát trễ |
| 20–35 | Tiếp tục, E nối day với gather/quan thật |
| 35–45 | `day --days 1`, chạy nhiều Ngày kiểm cấp nâng cấp, regression P1 với số chuẩn; `verify.py --phase 2`; `docs/verification/phase-2.md` |
| 45–50 | Retro nhanh trong `docs/retro.md` (điều tốt, điều vướng, 1 hành động có người nhận) |
| 50–55 | Dự phòng, Integrator đẩy tag `phase-2` |

## 5. Rủi ro
- **Lát 0 chậm → cả nhóm chờ.** Giảm: người khác viết test trước bằng scenario; lát 0 commit từng phần (contract.json + inventory trước).
- **3 lát cùng sửa `gather.py`** (1, 2 và step()) → chỉ sửa hàm mình sở hữu; A giữ thứ tự `step()` theo mục 4.5: đồng hồ → bơi, oxy, ngạt → quái + hit → tương tác → bắt cá → hết giờ → cá bơi, sinh cá.
- **Nợ quán P1 lớn** (lát 3+4) → C và D pair ở phút 0–5 để chốt cấu trúc khách (đã có khung trong contracts) trước khi tách.
- **Mode day phụ thuộc mọi lát** → E dựng day với sim hiện có ngay (khung chạy được dù luật chưa đủ), tích hợp dần.
- **Tất định**: cá bơi/sinh và chọn món phải dùng `Streams` với stream tách riêng; chạy `verify.py` trước mỗi merge lớn.
