# Kiểm các ví dụ TICKET-03 trên main — phase-3

- Commit: `0d4676c` · 2026-11-21 14:20
- Kết quả: **ĐẠT**

| Kiểm | Kết quả | Chi tiết |
|---|---|---|
| Fixture ngưỡng PRD (fresh 30, 1 bước) -> đúng dòng event mẫu | đạt | [{"type": "event", "tick": 1, "phase": "gather", "name": "spoiled", "data": {"item_id": "I1", "kind": "ca_linh", "location": "hold"}}] |
| Kho đếm / fresh 101 / id trùng / kind lạ -> mã 2 | đạt | [2, 2, 2, 2] |
| Day: bàn giao cùng tick không hao thêm; Ngày 2 id mới; ươn trong giỏ ở bước 8401 (đúng 30 sau 8400 bước, chưa ươn) | đạt | stock quán tick 0 = gather_end.inventory: True; id Ngày 2: ['I3', 'I4']; spoiled sau [8401] tick |
