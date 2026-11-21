# NTheBao — phản tư cá nhân

- **Phần tôi làm:** Vai PO; triển khai lát 3–4 cho điều phối Quán, hao tươi/đặt trước, rồi phase 4 bổ sung benchmark, soak 10 ngày và cảnh báo tương phản cao. Bằng chứng: commit `ec5e029`, `a62d9e2`; `docs/proof/phase-3/lit-3-4.md`, `docs/proof/phase-4/lit-3-4.md`.
- **Tôi đã giúp ai:** Phối hợp với nhóm qua vai PO, ghi rõ các giả định cần xác nhận để mọi người cùng kiểm tra, như công thức giá theo độ tươi và cách hiểu chỉ số benchmark. Bằng chứng: `docs/clarify.md`.
- **AI sai ở đâu, xác minh thế nào:** Khi sửa giao diện, AI để trùng khai báo `const stock`. Lỗi được phát hiện khi kiểm cú pháp JavaScript bằng Node và đã sửa; nhật ký ở `docs/ai-usage-log.md`. Bộ test sau đó chạy: 181 đạt, 46 bỏ qua.
- **Bài học / lần sau tôi sẽ:** Chốt các điểm contract còn mơ hồ sớm hơn; kiểm thử trực tiếp trên trình duyệt và lưu artifact benchmark/soak trước khi xác nhận bàn giao.
