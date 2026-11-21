# 06: Retro + ma trận AC-P4 + phản tư cá nhân

**What to build:** Bằng chứng để chấm: ma trận AC-P4-xx → bằng chứng → kết quả trên đúng commit tag, retro có rà hành động của Phase 2, và phản tư của từng người kèm dẫn chứng commit.

**Blocked by:** 01–04

**Status:** in-progress

- [x] `docs/verification/phase-4.md`: mỗi AC-P4 (bench, soak, cảnh báo, tương phản, clone sạch, release, regression P1–P3) có cách kiểm, link bằng chứng trong `docs/proof/phase-4/`, kết quả đạt/chưa đạt ghi trung thực (chỉ đánh dấu Đạt cho AC-P4-03 đã có artefact thật).
- [ ] Regression P1–P3 chạy lại trên commit tag; test nào đổi vì luật mới phải ghi lý do (chờ Integrator gắn tag và chạy test trên môi trường sạch).
- [x] `docs/retro.md`: **mở đầu bằng rà hành động đã chốt ở retro Phase 2** (đã làm chưa, vì sao), rồi điều tốt / điều tệ / hành động tiếp theo; nêu **một lỗi AI** và cách nhóm phát hiện.
- [ ] `docs/members/<handle>.md` đủ 5 người (≤ 200 từ), mỗi người tự viết dẫn chứng commit/bằng chứng cụ thể (hiện đã có `qvinhh2312.md` và `trandinhnhatminh1452.md`; 3 thành viên còn lại tự viết theo PRD §4).
- [x] `docs/ai-usage-log.md` và `docs/clarify.md` cập nhật cho Phase 4.
- [ ] Kiểm chéo: mỗi mục trong retro phải trỏ tới file/commit có thật trong repo chung.
