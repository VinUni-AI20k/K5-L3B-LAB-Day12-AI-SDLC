# trandinhnhatminh1452 — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm:
  - P1: hái/bắt cá, 25 test CLI, bàn giao PO; commit [2b95df8](https://github.com/PH31M/K5-L3B-LAB-Day12-AI-SDLC-MMMMV/commit/2b95df86c46e69e8f90bd1c6d1f378c0509f3754).
  - P2: cá bơi/sinh và vợt ([bằng chứng](../proof/phase-2/nhat-minh.md)).
  - P3: độ tươi, `spoiled`, ID/LIFO và dòng nước ([bằng chứng](../proof/phase-3/nhat-minh.md)).
  - Kiểm cuối: 104 test qua, 2 class skip (bản làm việc, contract v1.0); 174/174 qua khi ghép patch bàn giao trong thư mục tạm. P2–P3 **chưa commit/push/merge**.
- Tôi đã review: chưa có. Chưa có ai review P2–P3 của tôi, và tôi chưa review PR của Quang Vinh (theo vòng review).
- AI sai ở đâu và tôi phát hiện thế nào: probe giữ tham chiếu snapshot đến cuối nên vị trí cũ đổi theo bước sau. Tôi thấy khi so từng bước với assertion, rồi sửa để xuất JSONL ngay mỗi bước, giữ nguyên assertion. Console cp1258 cũng từng lỗi Unicode; log lưu UTF-8.
- Điều tôi học được:
  - Kiểm biên (đúng 1 m, đúng ngưỡng 30, số nguyên trước khi làm tròn) bắt được lỗi mà ca thường không thấy.
  - Test component qua probe không phải bằng chứng tích hợp sản phẩm: Stock v1.2, migration kho và vòng day/shop vẫn chưa kiểm.
  - Chỗ mơ hồ phải ghi thành giả định PO trong `docs/clarify.md` (Q1–Q8 vẫn chưa có xác nhận) thay vì tự quyết im lặng.
