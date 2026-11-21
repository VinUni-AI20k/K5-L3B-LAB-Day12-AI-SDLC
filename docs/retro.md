# Retro nhóm

## Phase 2 (nhanh)
> Nháp do PO (nganhduong123) dựng từ bằng chứng trong repo lúc `81b5aab`. Cả nhóm sửa/bổ sung trong buổi retro.

- Điều tốt:
  - Chia "nhà" theo hàm và giữ qua các phase: các lát cá bơi/sinh (Dũng), Q3 (Quốc), 2 bếp/6 món/`burn` (Kiên), UI (Dương) đều vào main qua PR nhỏ.
  - Test tăng từ 44 (P1) lên 96, toàn bộ đạt trên `81b5aab`. Mỗi lát có file test riêng (`test_p2_fish.py`, `test_p2_quan_lat3b.py`...).
  - UI không phải chờ sim: Shop, pause và `day` làm bằng mock theo trường snapshot đã chốt.
  - Script kiểm chứng tự thêm shim `python3`, nên máy Windows không còn báo fail giả (mã 9009).
- Điều tệ:
  - Lõi v1.1 chưa xong: `contract_version` còn `"1.0"`, chưa có `sim/day.py` (vòng ngày, Shop) và `sim/monsters.py` (Cá Sấu). Vì vậy chưa gắn được tag `phase-2`, còn Phase 3 và Phase 4 thì bị nợ dồn (bàn giao trong `day`, soak).
  - Đường găng dồn vào một người (Integrator vừa giữ số chuẩn vừa làm `day.py`).
  - Gộp muộn nên nhiều lần phải merge `main` và giải xung đột (`sim/quan.py`, `ai-usage-log.md`, `standup.md`).
  - Chưa review chéo: cả 7 PR đã gộp (#1–#7) đều không có review nào trên GitHub, dù thỏa thuận là người dự phòng review.
  - `docs/contracts/README.md` vẫn là template, giao diện chuyển pha chỉ nằm trong `docs/plan/phase-2.md`.
- 1 hành động cho Phase 3: **trả nợ v1.1 trước khi bật v1.2.** Bào đẩy số chuẩn v1.1 cùng adapter trước phút 12. Kiên (đã xong 3b) pair với Bào làm `day.py`. Người nhận: **invzble-z**. Minh kiểm lại ở standup phút 20.

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
