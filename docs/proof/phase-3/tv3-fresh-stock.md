# TV3 · Phase 3 — Kho cá thể, hao tươi, giữ lại (AC-P3-03)

```bash
PYTHONPATH=tests:. python3 -m unittest tests.test_quan_fresh_p3 -v
```

6/6 đạt. Suite toàn repo: 101/101.

| Yêu cầu | Kết quả |
|---|---|
| Hao 0.25/s; `fresh=30` ươn bước đầu; `spoiled` theo id, location=`stock` | Đạt |
| Giữ chỗ: tươi nhất rồi id | Đạt (I2 trước I3 khi cùng 95) |
| Phần giữ vừa ươn → nhả hết, thử giữ lại 1 lần; thiếu → `unfulfillable` | Đạt |
| Còn hàng tươi → giữ lại id mới | Đạt |
| Nấu tiêu đúng id; `base_price = floor(giá × avg_fresh/100)` | Đạt (hỗ trợ TV4) |
| Dual mode: kho đếm v1.1 vẫn chạy regression | Đạt |

Helper: [`chonoi/freshness.py`](../../../chonoi/freshness.py) (`decay_units`, `pick_for_recipe`, …).  
Tuning: `game.contract.json` → `tuning.freshness` (TV1 sẽ bump `contract_version` 1.2 khi adapter file sẵn sàng).

[Test](../../../tests/test_quan_fresh_p3.py)
