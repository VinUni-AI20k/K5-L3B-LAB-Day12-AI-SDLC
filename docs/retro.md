# Retro nhóm

## Phase 2 (nhanh)
> Nháp do PO (nganhduong123) dựng từ bằng chứng trong repo lúc `81b5aab`, cập nhật lúc `721088a` (sau lát 4a). Cả nhóm sửa/bổ sung trong buổi retro.

- Điều tốt:
  - Chia "nhà" theo hàm và giữ qua các phase: các lát cá bơi/sinh (Dũng), Q3 (Quốc), 2 bếp/6 món/`burn` (Kiên), UI (Dương) đều vào main qua PR nhỏ.
  - Test tăng từ 44 (P1) lên 96 (`81b5aab`), 119 (`721088a`) và 127 khi thêm `test_p2_ui_live.py`, toàn bộ đạt. Mỗi lát có file test riêng (`test_p2_fish.py`, `test_p2_quan_lat3b.py`...).
  - UI không phải chờ sim: Shop, pause và `day` làm bằng mock theo trường snapshot đã chốt. Khi `day.py` vào `main`, client chạy được cả vòng 2 Ngày với sim thật, chỉ phải sửa 4 lỗi nhỏ ở `live.py`/HUD (`docs/proof/phase-2/ui-day/`).
  - Script kiểm chứng tự thêm shim `python3`, nên máy Windows không còn báo fail giả (mã 9009).
- Điều tệ:
  - Lõi v1.1 xong muộn: số chuẩn v1.1 vào main ở `b85711d`, `sim/day.py` ở `721088a` (cuối phase). Vẫn chưa có `sim/monsters.py` (Cá Sấu), nên "Thủy quái!" chỉ thấy trên mock. Chưa gắn tag `phase-2`; Phase 3 và Phase 4 bị nợ dồn.
  - Đường găng dồn vào một người (Integrator vừa giữ số chuẩn vừa làm `day.py`).
  - Gộp muộn nên nhiều lần phải merge `main` và giải xung đột (`sim/quan.py`, `ai-usage-log.md`, `standup.md`).
  - Chưa review chéo: cả 11 PR đã gộp (#1–#11) đều có 0 review trên GitHub (`gh pr list --json reviews`), dù thỏa thuận là người dự phòng review. Lát 4a đẩy thẳng lên `main`, không qua PR.
  - Hợp đồng viết muộn (`bfb5160`, PR #10) nên code và hợp đồng đã lệch: `customer_id`/`order_id`, payload `paid`, `dish_burned`, `state:"running"` (`docs/contracts/README.md` mục 10). Thiếu đàn cá kèo nên kế hoạch D3–D5 không lấy đủ nguyên liệu (clarify #5).
  - Nhiều câu hỏi chờ PO quá lâu (Q3 D-01..D-09, Q4-F1, `no_dish`). PO chốt ở clarify #10–#15 lúc cuối phase.
- Trạng thái hành động (lúc `721088a`): `day.py` đã vào `main` (invzble-z, `721088a`), Kiên chưa pair. Adapter kho cá thể chưa có.
- Hành động bổ sung: **mỗi PR phải có 1 review của người dự phòng trước khi gộp** (Integrator không tự gộp PR chưa review). Người nhận: **invzble-z**, PO kiểm ở retro P4.
- 1 hành động cho Phase 3: **trả nợ Phase 2 trước khi bật v1.2.** Số chuẩn v1.1 đã có (`b85711d`). Bào đẩy adapter kho cá thể trước phút 12. Kiên (đã xong 3b) pair với Bào làm `day.py`. Người nhận: **invzble-z**. Minh kiểm lại ở standup phút 20.

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
