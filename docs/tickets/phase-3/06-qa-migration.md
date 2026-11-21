# 06: QA — migration, regression, ngưỡng 30

**What to build:** Một bộ test chứng minh việc đổi schema không làm hỏng gì: schema cũ bị từ chối đúng lúc, schema mới bắt đúng các nhánh tươi/ươn, và toàn bộ P1–P2 vẫn xanh.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] `tests/test_migration_v12.py`: file kho đếm ở v1.2 → mã 2; file cá thể ở v1.1 → mã 2; đọc/ghi vòng tròn giữ nguyên id, kind, fresh.
- [ ] Ca biên độ tươi: `fresh` đúng 30 ở tick 0 → `spoiled` tick 1; 30.0 so số nguyên; nhiều cá thể cùng vượt ngưỡng → thứ tự theo id.
- [ ] Ca hao: giỏ 2 đơn vị/tick, kho 1 đơn vị/tick, kẹp 0, hàng mới không hao ở bước nhận, pause dừng hao, món chín không hao.
- [ ] Ca giữ chỗ: con đang giữ vừa ươn → nhả toàn bộ + giữ lại một lần; không đủ → `unfulfillable`; hai đơn không dùng chung một id.
- [ ] Ca giá: trung bình lẻ → `floor`; boa trên giá đã chốt; điểm đúng công thức.
- [ ] Regression: chạy lại toàn bộ test P1–P2 trên schema mới; test nào bị thay phải ghi lý do trong commit và trong `docs/verification/phase-3.md`.
- [ ] `docs/verification/phase-3.md` đủ AC → cách kiểm → bằng chứng trong `docs/proof/phase-3/` → đạt/chưa đạt; ghi trung thực.
