# Bằng chứng lát 1 — oxy, ngạt, Máu, ngất (gather)

- **Nhánh:** `feat/lat-1`, tạo từ `cb2e298`. Chạy trên Windows, Python 3.11.9.
- **Code:** `chonoi/sim/gather.py` → `GatherSim._update_oxygen`.
- **Test:** `tests/test_gather_lat1.py`, gồm 13 test hộp đen qua `headless_cmd`.
- **Đối chiếu:** `docs/prd/phase-1.md` mục F "Gather" bước 2 và mục E.

## Ma trận yêu cầu → test

| Yêu cầu PRD-0 | Test | Kết quả |
|---|---|---|
| Dưới nước oxy −1 mỗi tick | `Oxygen.test_duoi_nuoc_tru_1_moi_tick` | đạt |
| Mặt nước (`d ≤ 0.5`) +`oxygen_refill_per_tick`, kẹp tối đa | `test_mat_nuoc_hoi_va_kep_toi_da`, `test_dung_mep_surface_depth_tinh_la_mat_nuoc` | đạt |
| `oxygen_empty` khi oxy từ dương xuống 0 (một lần) | `test_oxygen_empty_dung_mot_lan_khi_tu_duong_ve_0`, `test_khong_oxygen_empty_khi_da_bang_0_tu_dau` | đạt |
| Chạm 0 ở t → ngạt lần đầu ở t+59; đếm lại sau mỗi lần ngạt; `choke {hp}` | `Choke.test_cham_0_o_t_thi_ngat_o_t_cong_59` | đạt |
| Nổi lên đúng bước đáng lẽ ngạt thì hồi oxy, không ngạt | `test_noi_len_dung_buoc_dang_le_ngat_thi_khong_ngat` | đạt |
| Máu 0: bỏ giỏ LIFO, `faint {cause, lost, hp}` → `gather_end fainted`, kho rỗng, file kho `{"items":{}}` | `Faint.test_het_mau_bo_gio_lifo_va_kho_rong` | đạt |
| 3 Máu → ngất sau 3 lần ngạt | `test_ba_lan_ngat_moi_ngat_xiu` | đạt |
| Ngất xử lý trước hết giờ (cùng tick → `fainted`) | `test_ngat_xiu_thang_het_gio_cung_tick` | đạt |
| `dive` / `surface` chỉ khi đổi phía, `pos` sau di chuyển | `DiveSurface.*` | đạt |
| Tất định từng byte | `test_tat_dinh_tung_byte` | đạt |

Toàn bộ bộ test (`PYTHONPATH="tests;." python3 -m unittest discover -s tests`): **45 test, OK**.
Output đầy đủ của 13 test lát 1 nằm trong [`lat1-unittest.txt`](lat1-unittest.txt).

## Chạy thật: lặn xuống và không bao giờ nổi lên

```
echo '{"frames":[{"tick":0,"move":[0,1]}]}' > dive.json
python3 -m chonoi.headless --mode gather --seed 1 --ticks 6000 --inputs dive.json --inventory-out kho.json --out run.jsonl
```

Chạy hai lần: cả hai đều thoát với mã 0, hai file JSONL giống nhau từng byte (`cmp`). Các sự kiện ghi được:

| tick | sự kiện | data |
|---|---|---|
| 11 | `dive` | `{"pos":[2.0,0.567]}` |
| 1810 | `oxygen_empty` | `{"oxygen_ticks":0}` (1800 tick oxy, từ tick 11 đến 1810) |
| 1869 | `choke` | `{"hp":2}` (= 1810 + 59) |
| 1929 | `choke` | `{"hp":1}` |
| 1989 | `choke`, `faint`, `gather_end` | `{"hp":0}`, `{"cause":"choke","lost":[],"hp":0}`, `{"reason":"fainted","inventory":{"items":{}}}` |

- Dòng `end`: `"ticks":1989, "reason":"fainted"`.
- `kho.json`: `{"items":{}}`.
