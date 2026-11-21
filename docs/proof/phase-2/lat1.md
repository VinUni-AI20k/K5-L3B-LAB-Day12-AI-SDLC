# Bằng chứng lát 1 Phase 2: Cá Sấu Năm Chèo, Máu và ngất (AC-P2-03)

- **Code:** `chonoi/sim/gather.py` gồm `_update_monsters`, `_faint` (dùng chung với `_update_oxygen`), `_clamp_monster`, `_toward`.
  - Gọi trong `step()` ngay sau oxy/ngạt, theo Ticket-02 mục 4.5.
- **Test:** `tests/test_gather_lat1_p2.py`, gồm 14 test hộp đen. Output đầy đủ: [`lat1-unittest.txt`](lat1-unittest.txt).
- **Toàn bộ bộ test sau khi thêm lát 1:** 160 test, OK.

| Luật (docs/prd/phase-2.md mục 1.2) | Test | Kết quả |
|---|---|---|
| `patrol` 1 m/s tới waypoint, tới nơi thì đổi mục tiêu; gather độc lập dùng bố trí Ngày 1 | `Patrol.*` | đạt |
| `chase` 3 m/s khi người chơi ở `d ≥ 10` và cách ≤ 10 m; không đuổi khi `d < 10`; về `patrol` khi cách > 16 m | `Chase.*` | đạt |
| Cắn: −1 Máu, rơi `floor(n/2)` món theo LIFO, bất tử 90 tick, phát `monster_hit {monster_id, hp, lost, pos}` | `Hit.test_cham_mat_mau_rot_nua_gio_lifo_bat_tu_va_recoil` | đạt |
| `recoil` 60 bước tính từ bước sau, mỗi bước 2/60 m ra xa người chơi; trùng tâm thì dùng +x; hết `recoil` thì về `patrol` | như trên, `test_trung_tam_thi_recoil_theo_x_duong` | đạt |
| Còn bất tử thì không bị cắn (kể cả bất tử dựng từ scenario) | `test_bat_tu_*`, `test_invuln_tu_scenario_*` | đạt |
| Mỗi bước tối đa một cú cắn: con gần nhất, hòa thì theo id; con không cắn thì không vào `recoil` | `test_moi_buoc_toi_da_mot_hit_*` | đạt |
| Ngạt xuyên bất tử và không làm rơi hàng | `test_ngat_xuyen_bat_tu_va_khong_rot_hang` | đạt |
| Hết Máu do quái: `monster_hit` → `faint {cause: "monster"}` → `gather_end fainted`, kho `{"items":{}}` | `Faint.test_het_mau_do_ca_sau_*` | đạt |
| Cùng tick: ngạt trước rồi mới bị cắn | `test_ngat_cung_tick_di_truoc_hit` | đạt |
| Tất định từng byte | `test_tat_dinh` | đạt |

**Kiểm test có bắt lỗi không:** cố tình bỏ dòng chặn bất tử thì 3 test đỏ; trả code lại thì xanh.

**Hiệu năng:** `--mode day --days 1` (22.200 tick, người chơi lặn xuống rồi bơi ngang) chạy hết khoảng 0,6 s, dưới mức ≤ 20 s.
- Sự kiện ghi được: `choke` → `monster_hit {M1, hp: 1}` → `choke` → `faint {cause: "choke"}` → `gather_end fainted`.

**Giả định** (đã ghi vào `docs/clarify.md`):
- Khoảng cách để chuyển `patrol` ↔ `chase` đo **trước** khi con sấu di chuyển trong bước.
- Ngưỡng độ sâu để bị phát hiện và bị cắn lấy `depths[0]` của loài, tức 10 với Cá Sấu.
