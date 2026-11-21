# 01: Contract v1.1 + schema/CLI/envelope (prefactor)

**What to build:** Nâng hợp đồng lên v1.1 để bốn lát sau chạy song song mà không ai phải sửa cùng một file: số liệu chuẩn, khóa manifest mới, `--mode day --days N`, scenario nhận khối `day`/`monsters`/`ca_ho`, snapshot và event mang thêm `day`. Sau ticket này, `--mode day` chạy được ở mức khung (chưa có luật ngày).

**Blocked by:** — (chỉ sau khi `main` đã tag `phase-1`)

**Status:** ready-for-agent

- [ ] `contract_version: "1.1"`; `fish_initial` là **8 đàn**; đủ khóa mới `fish_speed, fish_turn_ticks, fish_max, fish_spawn_ticks, fish_spawn_clearance, fish_x, fish_depths, fish_spawn_x, fish_spawn_depths, fish_weights`; `fish_yield` và các map theo loài có đủ `ca_linh, ca_loc, ca_keo`.
- [ ] `gather.nodes` có N5/N6 (`keo_neo`); `gather.monsters` có `ca_sau` + 2 spawn M1/M2 (`from_day`) + `invuln_ticks: 90`, `loss_ratio: 0.5`; `quan` có B2, T2–T4; `menu` có 6 món; `day_plan` 5 Ngày; `shop` có `max_ticks`, `upgrades.oxygen/hp`; `extensions: ["net"]`.
- [ ] `KINDS_P1` thêm `ca_keo`, `keo_neo`; `contract.py` bỏ ràng buộc "đúng 6 đàn", thêm kiểm dải mới; `burn_s` vẫn phải `null` (chưa bật Cháy).
- [ ] `--mode day` chạy mã 0 với `--ticks 0`; `--days` chỉ dùng với `day`, nguyên 1..5 (sai → mã 2).
- [ ] Scenario: khối `day {money, earned, reputation, upgrades, day_plan}`; `gather.monsters[]`, `gather.ca_ho`, `fish[].age_ticks`, `player.invuln_ticks/attack_cd_ticks`; `quan.stock`/`quan.reputation` trong `day` → mã 2.
- [ ] Snapshot/event trong `day` có thêm `day, day_plan, upgrades, active_upgrades`; vỏ event có `day`; `state: "paused"` hợp lệ.
- [ ] Test P1 phải sửa **kèm lý do trong commit**: `fish_initial` 6 → 8, `--mode day` không còn bị từ chối. Ghi lý do vào `docs/verification/phase-2.md`.
