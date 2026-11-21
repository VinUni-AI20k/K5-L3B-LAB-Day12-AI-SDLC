# Kiểm chứng P2-10: hồi quy Phase 1 và smoke `day`, `pause`

Chạy ngày 2026-11-21 trên Windows (Python 3.13) ở `main` sau PR #30 (có P2-04, P2-05, P2-06, P2-07, P2-09). Smoke gọi `headless_cmd` thật (hộp đen).

## Lệnh và kết quả

```
PYTHONPATH=tests:. python -m unittest discover -s tests   # Ran 250 tests in 20.056s, OK
python tools/smoke_phase1.py                              # 27/27 mục đạt (hồi quy Phase 1)
python tools/check_no_hardcode.py                         # OK
python tools/check_determinism.py                         # gather, quan, day giống từng byte (day: 2 Ngày đầy đủ)
python tools/smoke_phase2.py                              # 15/15, bảng bên dưới
```

## Kết quả `tools/smoke_phase2.py`

```
OK   gather -> kho: file kho = hold dựng sẵn                     mã 0, kho {'items': {'bong_dien_dien': 1, 'bong_sung': 2, 'ca_keo': 1, 'ca_linh': 2, 'ca_loc': 1, 'keo_neo': 1}}
OK   quan v1.1: tick 0 có 2 bếp, 4 bàn, stock = kho              mã 0, 2 bếp, 4 bàn
OK   quan: có khách đến, mọi món gọi nằm trong menu 6 món        7 khách, 6 món menu
OK   quan: ca đủ 10800 tick kết thúc quan_end                    {'type': 'end', 'ticks': 10800, 'sim_tick': 10800, 'mode': 'quan', 'state': 'finished', 'reason': 'time', 'money': 0, 'earned': 0, 'reputation': 1.0, 'score': 100}
OK   ca gather đủ -> quán đủ: mã 0 và giống từng byte qua 2 lần  
OK   gather: có fish_spawned (cá thể sinh động, P2-03)           4 sự kiện
OK   gather: pause -> paused, đứng yên, resumed                  mã 0, sự kiện ['paused', 'resumed']
OK   quan: pause -> paused, đứng yên, resumed                    mã 0, sự kiện ['paused', 'resumed']
OK   day: thứ tự sự kiện qua 2 Ngày đúng mục 4.5                 mã 0, 16 sự kiện
OK   day: kết thúc days_complete, days_completed = 2             {'type': 'end', 'ticks': 44400, 'sim_tick': 44400, 'mode': 'day', 'state': 'finished', 'reason': 'days_complete', 'money': 0, 'earned': 0, 'reputation': 3.0, 'score': 300, 'days_completed': 2}
OK   day: tất định từng byte qua 2 lần                           
OK   day: snapshot có day, day_plan, upgrades, active_upgrades   khóa ['active_upgrades', 'day', 'day_plan', 'earned', 'mode', 'money']
OK   day: --days 0 -> mã 2                                       mã 2
OK   day: --days 6 -> mã 2                                       mã 2
OK   day: --inventory với day -> mã 2                            mã 2

15/15 mục đạt
```

## Ghi chú
- Hồi quy Phase 1: `tools/smoke_phase1.py` vẫn 27/27; mục "--mode day bị từ chối" của v1.0 đã đổi thành "--days với gather" (day nay hợp lệ, lý do ở PR #28).
- `check_determinism.py` nay gồm `day` (`--days 2`, chạy hết `days_complete`, bỏ qua `--ticks`).
- Chưa phủ ở smoke hộp đen: mua đồ ở Shop (`buy`) và `chonoi.live` ở chế độ day (P2-08); `buy` được kiểm ở `tests/test_p2_day.py`.
