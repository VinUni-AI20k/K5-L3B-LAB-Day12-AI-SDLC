# thanhvu101 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (Phase 1–4, nhánh `M5`):**
  - **Phase 1**: Cập nhật `AGENTS.md`, xây dựng 2 skill (`.agents/skills/verify-phase/`, `ui-contract-sync/`), chốt `docs/ui-contract.md`, xây HUD `gather`/`quan` trên `chonoi.live` và tích hợp sửa lỗi thu hoạch M2.
  - **Phase 2**: Xây đủ luồng màn hình (`Main Menu` → `DayIntro` → `Gather` → `EveningIntro` → `Quan` → `DayResult & Shop` → `Summary` + `Pause`), hỗ trợ 2 bếp (`B1`, `B2`) & 4 bàn (`T1`–`T4`), phím kết thúc ca sớm (`F`), camera phóng to bám Út Sen và hoạt ảnh Canvas 2D shapes cho Út Sen (thợ lặn chuyển hướng + phụ bếp), cá bơi, bụi bông, bếp lửa/khói.
  - **Phase 3**: Viết dual-schema adapter trong `chonoi/web/index.html` đọc cả kho đếm v1.0/v1.1 lẫn kho cá thể `{id, kind, fresh}` v1.2, hiển thị thanh độ tươi & cảnh báo hàng ươn `☠`.
  - **Phase 4**: Xây `chonoi/bench.py` xuất 5 trường `bench.json`, hoàn thiện 3 cảnh báo (thủy quái, oxy, khách giận), chế độ tương phản cao `[H]` và mở rộng phụ đề SFX `[C]`.
- **AI sai ở đâu và cách xác minh:** Bộ gõ tiếng Việt (Telex/VNI) làm `e.key` lệch khi nhấn giữ phím; đã đổi sang mã vật lý `e.code` và kiểm chứng bằng `tests/test_live_m5.py`.
- **Bài học:** Tách sạch tầng UI (`chonoi/web/`) khỏi `sim` giúp nâng cấp animation, màn hình và accessibility suốt 4 phase mà không phá tính tất định headless.
