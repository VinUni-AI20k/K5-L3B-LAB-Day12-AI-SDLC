# ThanhDNQ — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit):
  + Triển khai toàn bộ logic Lát 4 Quán (bếp nấu, bưng bê, phục vụ tại bàn, tính tiền, boa, uy tín, đóng ca) trong `chonoi/sim/quan.py`.
  + Xây dựng bộ test `tests/test_p1_quan_service.py` kiểm thử 6 kịch bản theo PRD-0 và tạo bằng chứng kiểm chứng `docs/proof/phase-1/nguoi-4/service_proof.txt`.
- Tôi đã review (kèm link):
  + Rà soát và chuẩn bị kết nối giao diện tích hợp với Người 3 (`quan_customers.py`) theo [docs/plan/phase-1-integration.md](../plan/phase-1-integration.md).
- AI sai ở đâu và tôi phát hiện thế nào:
  + AI ban đầu đưa bàn `T2` vào fixture test đóng ca, trong khi contract Phase 1 chỉ có bàn `T1`, khiến runner văng mã lỗi 2. Tôi phát hiện qua log chạy test và điều chỉnh lại đúng quy chuẩn.
- Điều tôi học được:
  + Thiết kế ranh giới module rõ ràng và fallback stubs giúp phát triển song song mượt mà, không bị nghẽn khi các thành viên khác đang làm việc trên nhánh riêng.
