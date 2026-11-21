# NTLam108 — phản tư cá nhân (≤ 200 từ)

TV4, Developer Quán (Phase 1: Lát 4; Phase 2: mode `day`).

- **Tôi đã làm (kèm link commit):**
  - Phase 1: chốt phân vùng `quan.py` với TV3 ([f3331af](https://github.com/Hphong2305/K5-L3B-LAB-Day12-AI-SDLC-439/commit/f3331af)). Lát 4 (bếp, bưng, phục vụ, tiền, boa, uy tín), ghép `step()`, script E2E ([45c7733](https://github.com/Hphong2305/K5-L3B-LAB-Day12-AI-SDLC-439/commit/45c7733)). Sửa thời hạn món thừa, ADR-0001 ([070ab9b](https://github.com/Hphong2305/K5-L3B-LAB-Day12-AI-SDLC-439/commit/070ab9b)).
  - Phase 2: mode `day`: vòng ngày, Shop, nâng cấp, pause, 10 test ([c82f599](https://github.com/Hphong2305/K5-L3B-LAB-Day12-AI-SDLC-439/commit/c82f599)).
- **Tôi đã review (kèm link):**
  - Lát 3 của TV3 ([78ab793](https://github.com/Hphong2305/K5-L3B-LAB-Day12-AI-SDLC-439/commit/78ab793)): chạy lại lệnh proof, trùng SHA-256.
  - Món thừa của TV3 ([ce83005](https://github.com/Hphong2305/K5-L3B-LAB-Day12-AI-SDLC-439/commit/ce83005)): phát hiện thời hạn tính sai, số liệu nằm ngoài contract, sửa `live.py` chưa ghi lý do.
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - Bếp nhận đơn `assigned` trong khi TV3 dùng `waiting`. Phát hiện khi đọc diff.
  - Khách rời khi món đang nấu làm kẹt quán (Q7). Script E2E bắt được qua kiểm bất biến.
  - 30 phút game bị tính như 30 phút thật, dài hơn cả ca. Tôi quy đổi lại: 30 phút game = 1800 tick.
- **Điều tôi học được:** chốt interface và tên trạng thái bằng văn bản trước khi code. Kiểm bất biến từng tick bắt được lỗi ở ranh giới hai lát mà unit test riêng lẻ bỏ sót.
