# Ma trận truy vết Phase 2

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Contract v1.1 | `load_contract()` kiểm version, 2 bếp, 4 bàn, 6 món, 5 ngày, shop | `tests/test_monsters.py::MonsterContractTests::test_contract_v11_has_core_phase2_values` | Đạt |
| 6 nguyên liệu | Nạp file kho chứa `ca_keo`, `keo_neo` | `tests/test_monsters.py::MonsterContractTests::test_inventory_accepts_new_v11_ingredients` | Đạt |
| Scenario Cá Sấu | Từ chối quái đặt ở độ sâu dưới ngưỡng; kiểm trường/độ sâu quái | `tests/test_monsters.py::MonsterContractTests::test_monster_scenario_must_be_underwater` | Đạt |
| M1 hit / LIFO / recoil / invuln | Va chạm giảm 1 Máu, mất 1 nửa giỏ theo LIFO, recoil 60 tick, invulnerability 90 tick | `tests/test_monsters.py::MonsterSimulationTests::test_m1_hit_removes_lifo_half_and_sets_invuln_recoil` | Đạt |
| M1 faint | HP về 0 phát `faint(cause="monster")` và `gather_end(fainted)`, giỏ rỗng | `tests/test_monsters.py::MonsterSimulationTests::test_m1_faint_clears_hold_and_emits_gather_end` | Đạt |
| M1/M2 theo Ngày | M1 Ngày 1, M2 Ngày 3 | `tests/test_monsters.py::MonsterSimulationTests::test_m2_only_active_on_day3` | Đạt |

## Đánh giá ngắn

- Phần Nhung đã hoàn thành: contract v1.1, kho 6 nguyên liệu, Cá Sấu M1/M2, scenario v1.1 và hợp đồng sự kiện.
- `game.contract.json` giữ số liệu từ contract thay vì hard-code trong luật.
- Phần `--mode day`, Shop, Pause, Hook UI và lát quán thuộc đầu việc của người khác.
- Kết quả tự động: `python3 -m unittest discover -s tests -v` — 39 tests, 39 pass.
- Smoke gather tick 0: `python3 -m chonoi.headless --mode gather --seed 1 --ticks 0 --out docs/proof/phase-2/gather-smoke.jsonl` — pass.
- Kiểm danh sách nhóm: `python tools/check_team.py` — OK, 6 thành viên.
