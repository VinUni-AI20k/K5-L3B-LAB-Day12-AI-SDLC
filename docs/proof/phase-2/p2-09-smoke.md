# Kiểm chứng P2-09: smoke tích hợp phút 20 (gather -> kho -> quán v1.1)

Chạy ngày 2026-11-21 trên Windows (Python 3.13) ở `main` sau PR #26 (có P2-02, P2-03, P2-05, P2-06). Chỉ gọi `headless_cmd` thật (hộp đen).

## Lệnh

```
python tools/smoke_phase2.py
```

## Kết quả

```
OK   gather -> kho: file kho = hold dựng sẵn                     mã 0, kho {'items': {'bong_dien_dien': 1, 'bong_sung': 2, 'ca_keo': 1, 'ca_linh': 2, 'ca_loc': 1, 'keo_neo': 1}}
OK   quan v1.1: tick 0 có 2 bếp, 4 bàn, stock = kho              mã 0, 2 bếp, 4 bàn
OK   quan: có khách đến, mọi món gọi nằm trong menu 6 món        7 khách, 6 món menu
OK   quan: ca đủ 10800 tick kết thúc quan_end                    {'type': 'end', 'ticks': 10800, 'sim_tick': 10800, 'mode': 'quan', 'state': 'finished', 'reason': 'time', 'money': 0, 'earned': 0, 'reputation': 1.0, 'score': 100}
OK   ca gather đủ -> quán đủ: mã 0 và giống từng byte qua 2 lần  
OK   gather: có fish_spawned (cá thể sinh động, P2-03)           4 sự kiện

6/6 mục đạt
```

## Ghi chú
- Chưa kiểm `pause` và `--mode day`: nằm ở nhánh P2-07 (PR #28), sẽ thêm vào smoke ở P2-10 sau khi gộp.
- Quán chạy độc lập không có người chơi nên không phục vụ món nào; mục này chỉ kiểm luồng bàn giao, bố cục quán v1.1 và tính tất định.
