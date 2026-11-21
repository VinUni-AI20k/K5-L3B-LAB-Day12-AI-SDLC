# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | Người 3 | Codex | Rà starter, viết khách/đơn/kho và test | Chưa có số liệu | Lab board hiện chưa phát hành PRD-0 trong phiên kiểm tra; các giả định được ghi ở `docs/clarify.md`. |
| 1 | Người 3 | Codex | Đối chiếu tài liệu PRD-0, sửa logic và chạy lại test | Chưa có số liệu | Bản đầu ghi tồn khả dụng vào snapshot và cho khách rời trước tương tác. PRD-0 mục D–F xác nhận snapshot ghi tồn vật lý và khách rời sau tương tác. |
| 1 | Thành viên 4 — Kitchen & Serving (chưa cung cấp handle) | Codex | P1-04: helper bếp/phục vụ/thanh toán, fixture, unit/headless/HTTP test, đối chiếu PRD-0 | Không đo | 68 test pass; đã sửa giả định order_id/items theo PRD bổ sung và lỗi số thực tại mép bán kính. Bằng chứng: docs/proof/phase-1/P1-04-results.json; dependency P1-03 ghi trong docs/notes/P1-04.md. |
