# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | ttkien0710 (Trần Trung Kiên) | Gemini 3.8 Flash (High) | Viết logic sim/quan Lát 4 (bếp, phục vụ, thanh toán, tip, quan_end) và bộ test unit 7 cases | ~30k tokens | AI viết thiếu thả nút interact giữa 2 lần bấm trong test, phát hiện nhờ assertion error và đã sửa đúng cơ chế cạnh lên |
| 1 | NhomF7 / Copilot | Copilot SDK trong VS Code | Hoàn thiện Gather, Quán, test logic và verification | Không đo được | Đã đối chiếu contract trước sửa; test baseline và suite sau sửa đều xanh. |
| 2 | ttkien0710 (Trần Trung Kiên) | Gemini 3.8 Flash (High) | Cài đặt Quán Lát 3b Phase 2 (2 bếp, ưu tiên đơn cũ nhất, menu 6 món, dọn ca, mở rộng burn) và 7 unit tests | ~35k tokens | AI chọn nhầm idle stove khi tay đang cầm đĩa khiến tương tác bàn bị chặn; đã phát hiện qua test_nearest_interaction_priority và sửa hàm _interact duyệt qua candidate tương tác hợp lệ |
