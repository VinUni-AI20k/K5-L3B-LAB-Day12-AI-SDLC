# Definition of done — Phase 2 Q3

- [x] Interface khách, filter, lịch, reservation, order_tick và test có proof.
- [x] Review Q4 và ghi finding có thể tái hiện.
- [ ] Q3/Q4 đã ghép và test hai bếp; các regression hiện có đạt, nhưng Q4-F1 vẫn tái hiện và chưa có chính sách được duyệt.
- [ ] Manifest v1.1 đã có; DaySim thật được kiểm bằng integration test và headless 1/3 ngày. T07 còn PARTIAL vì filter rỗng, reputation qua ngày và `sim_tick` khi pause.
- [ ] PO/Integrator xác nhận AC, no_dish và schema; QA nghiệm thu.
- [ ] Quốc xác nhận phản tư cá nhân và reviewer chấp nhận bàn giao.

[Proof lịch sử sau merge](../../docs/proof/phase-2/q3/postmerge-baseline-63f850e.txt); kiểm chứng tích hợp mới: [day-integration-5b79199.txt](../../docs/proof/phase-2/q3/day-integration-5b79199.txt), [day-regression-5b79199.txt](../../docs/proof/phase-2/q3/day-regression-5b79199.txt), [findings](../../docs/proof/phase-2/q3/day-findings.md). Có 5 expected failures có chủ đích cho lỗi thuộc DaySim/Runner; do đó không hàm ý Day hoặc QA đã nghiệm thu.
