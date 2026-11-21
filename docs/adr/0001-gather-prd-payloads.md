# 0001 — Hiệu chỉnh Gather Core theo PRD-0

Ngày: 2026-11-21. Người thực hiện: Phạm Lý Ngọc Đức (`Ducbaynao`).

Trạng thái: tôi đã triển khai và kiểm chứng trên nhánh `fix/ducbaynao-gather-prd-payloads`, chờ Integrator review trước khi merge. Đây không phải biên bản nhóm đã phê duyệt.

Tôi đối chiếu bản “PRD-0 — Quán Ăn Chợ Nổi (Phase 1), Test Contract v1.0” do người dùng cung cấp với hợp đồng nội bộ. Mục E quy định `oxygen_empty` có `oxygen_ticks:0`; `faint` có `cause:"choke",lost,hp:0`, với `lost` theo thứ tự bỏ LIFO. Mục F yêu cầu nhận đủ yield hoặc từ chối toàn bộ. Mục G yêu cầu ngất ghi kho rỗng khi có `--inventory-out`.

Tôi sửa hai payload, lưu bản đảo giỏ trước khi xóa và đổi helper giỏ sang nhận đủ lô hoặc trả 0. Hai đường hái/bắt cá dùng cùng helper sau bước kiểm tra chỗ trống của TV3. Tôi cập nhật bảng Gather trong hợp đồng, giải đáp lại clarify 3–4 và bổ sung test CLI. Việc sửa kỳ vọng test là do kỳ vọng cũ sai mục E/F của PRD, không phải để bỏ qua lỗi luật.

Tôi không thay tuning, schema kho hay luật quán. Các trường `amount`, `yield` và payload `hold_full` trong tài liệu Gather được đồng bộ với PRD và code TV3 hiện có. Bảng quán cần chủ module đối chiếu riêng.

Tôi giữ log bàn giao cũ để truy vết; [bằng chứng hiệu chỉnh](../proof/phase-1/member-2/prd-correction/summary.json) là kết quả mới. Cách tái chạy và giới hạn kết luận nằm trong [báo cáo TV2](../proof/phase-1/member-2/README.md).
