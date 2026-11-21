# Bằng chứng — TV2: quán lát 3 + kiểm fixture/contract (2026-11-21, đã đối chiếu PRD-0)

## Test

```
$ PYTHONPATH=tests:. python3 -m unittest discover -s tests
Ran 51 tests in 5.150s
OK
```
32 test starter + 19 test trong `tests/test_quan_lat3.py` (Arrivals, Leaving, Fixtures chạy hộp đen qua `headless_cmd`; Units gọi `QuanSim`/`validate_tuning`).
Riêng `test_fixture_mau_thuan_exit_2` có 44 fixture sai; đã in stderr từng ca để chắc mỗi ca thoát mã 2 đúng lý do (không phải lỗi phụ).

| Luật PRD-0 | Test |
|---|---|
| F5 lượt khách ở `first_customer_tick`, bàn trống id nhỏ nhất, giữ đúng công thức, order_tick = phase_tick, kiên nhẫn giảm từ bước sau | `test_khach_dau_tien_den_dung_first_customer_tick` |
| D lịch theo phase_tick kể cả khi rút ngắn ca | `test_lich_theo_phase_tick_ke_ca_khi_rut_ngan_ca` |
| E `no_dish {}`; D `random_customers:false` | `test_no_dish_data_rong_…`, `test_random_customers_false_…` |
| D id mới nối sau hậu tố lớn nhất; F4 rời bàn nhả phần giữ | `test_id_khach_moi_noi_tiep_…` |
| F4 hết kiên nhẫn → `customer_left patience` + uy tín; E data | `test_het_kien_nhan_roi_ban_tru_uy_tin` |
| F4 hết ca → `closing`, không trừ uy tín, dọn xong mới `quan_end` | `test_het_ca_khach_cho_roi_closing_…` |
| F4 khách rời bỏ món của đơn trên bếp / tay | `test_khach_roi_bo_mon_cua_don_tren_bep_va_tay` |
| D mặc định khách, reserved cấp theo công thức; giữ quá tồn → 2 (cả `--inventory`) | `Fixtures.*` |
| F5 chọn đều theo seed; hết bàn bỏ lượt; uy tín kẹp min | `Units.*` |
| A cố định 3 món + công thức, 1 bếp B1, 1 bàn T1 | `test_contract_co_dinh_mon_bep_ban` |
| E cùng seed → giống từng byte | `test_tat_dinh_cung_seed` |

## Chạy headless cả ca (chưa có lát 4 nên chưa ai phục vụ)

```
$ echo '{"quan":{"stock":{"ca_loc":2,"bong_sung":2}}}' > sc.json
$ python3 -m chonoi.headless --mode quan --seed 1 --ticks 10800 --scenario sc.json --snapshot-every 100000 --out q.jsonl
exit 0
{"type":"event","tick":120,"name":"customer_arrived","data":{"order_id":"C1","table_id":"T1","dish_id":"ca_loc_nuong_trui"}}
{"type":"event","tick":3720,"name":"customer_left","data":{"order_id":"C1","table_id":"T1","reason":"patience","reputation":2.5}}
{"type":"event","tick":3720,"name":"customer_arrived","data":{"order_id":"C2","table_id":"T1","dish_id":"ca_loc_nuong_trui"}}
{"type":"event","tick":7320,"name":"customer_left","data":{"order_id":"C2","table_id":"T1","reason":"patience","reputation":2.0}}
{"type":"event","tick":7320,"name":"customer_arrived","data":{"order_id":"C3","table_id":"T1","dish_id":"ca_loc_nuong_trui"}}
{"type":"event","tick":10800,"name":"customer_left","data":{"order_id":"C3","table_id":"T1","reason":"closing","reputation":2.0}}
{"type":"event","tick":10800,"name":"quan_end","data":{"reason":"time","money":0,"earned":0,"shift_earned":0,"reputation":2.0}}
{"type":"end","ticks":10800,"sim_tick":10800,"mode":"quan","state":"finished","reason":"time","money":0,"earned":0,"reputation":2.0,"score":200}
```
(Lược trường `phase`.) 120 = `first_customer_tick`; lượt 1020/1920/2820 bị bỏ vì T1 có khách; 3720 = 120 + 4·900 trùng lúc C1 rời nên C2 ngồi ngay cùng tick.
C3 còn chờ lúc hết ca → `closing`, uy tín giữ 2.0. Điểm = 0 + 100·floor(2.0) = 200.

## Mâu thuẫn → mã 2, không ghi JSONL

```
$ echo '{"quan":{"stock":{},"customers":[{"id":"C1","table_id":"T1","dish_id":"ca_loc_nuong_trui"}]}}' > bad.json
$ python3 -m chonoi.headless --mode quan --seed 1 --ticks 0 --scenario bad.json --out b.jsonl
đầu vào sai: khách giữ chỗ quá tồn kho (thiếu {'ca_loc': 1})
exit 2
```

## Chưa làm / còn mở
- Lát 4 (TV3): nấu, bưng, phục vụ, `paid`, boa — các chỗ `TODO(nhóm, lát 4 — TV3)` trong `chonoi/sim/quan.py`.
- Câu hỏi Q14–Q19 trong `docs/clarify.md` chưa hỏi Anh Năm.
