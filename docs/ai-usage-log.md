# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | lunaHieu | Gemini Web UI (tên model chờ xác nhận) | Chuỗi khoảng 10 lượt: phân tích PRD-0 và Test Contract v1.0; soạn AC-P1-G2-01..05; tạo prompt giới hạn phạm vi cho Codex; review diff code và kết quả kiểm chứng. | Người dùng ước tính khoảng 22.000 token trao đổi trực tiếp (14.000 input, 8.000 output), khoảng 55.000 nếu tính ngữ cảnh lịch sử; $0 qua bản web. | Dùng spec, diff và test thật để kiểm soát đầu ra; chưa có tên model hiển thị nên không đoán. |
| 1 | lunaHieu | Codex (GPT-6) | Đọc hướng dẫn, PRD-0, phân công và repo; đối chiếu phạm vi Lát 2 với khung Python. | Khoảng 8.000–15.000 token, ước tính thô; chi phí không có số đo. | Ban đầu đánh giá vai Người 5 quá dễ; kiểm lại phạm vi và sửa khuyến nghị thành Người 2. |
| 1 | lunaHieu | Codex (GPT-6) | Phân tích ranh giới với Người 1, viết đặc tả Lát 2 trong `docs/plan/phase-1.md`, rà từng AC và kế hoạch test. | Khoảng 8.000–15.000 token, ước tính thô; chi phí không có số đo. | Codex thêm helper `_nearest()` ngoài hai khối TODO; phát hiện bằng `git diff`, hoàn tác trước khi triển khai. |
| 1 | lunaHieu | Codex (GPT-6) | Điền hai khối TODO Lát 2, tạo 15 test, chạy toàn suite, lưu output và cập nhật ma trận kiểm chứng. | Khoảng 15.000–30.000 token, ước tính thô; chi phí không có số đo. | 46/47 test đạt; test ngất thất bại do Lát 1 chưa xử lý `choke`/`faint`. Giữ nguyên test, không làm xanh giả. |
| 1 | lunaHieu | Codex (GPT-6) | Bổ sung README, nhật ký AI và phản tư cá nhân theo kết quả Git và test thực tế. | Khoảng 5.000–10.000 token, ước tính thô; chi phí không có số đo. | Rà lại commit và proof trước khi ghi tài liệu; không sửa code Python trong lượt này. |
| 1 | Người 3 | Codex | Rà starter, viết khách/đơn/kho và test | Chưa có số liệu | Lab board hiện chưa phát hành PRD-0 trong phiên kiểm tra; các giả định được ghi ở `docs/clarify.md`. |
| 1 | Người 3 | Codex | Đối chiếu tài liệu PRD-0, sửa logic và chạy lại test | Chưa có số liệu | Bản đầu ghi tồn khả dụng vào snapshot và cho khách rời trước tương tác. PRD-0 mục D–F xác nhận snapshot ghi tồn vật lý và khách rời sau tương tác. |

Ước tính Codex là khoảng rộng dựa trên nội dung trao đổi, không phải số token đo từ ứng dụng hoặc hóa đơn. Thông tin Gemini do `lunaHieu` cung cấp; cập nhật tên model khi có tên hiển thị chính xác.
