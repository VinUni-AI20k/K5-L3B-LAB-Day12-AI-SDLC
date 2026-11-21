# 07: Verification pack — test biên, smoke hai tiến trình, bằng chứng

**What to build:** Một lệnh chạy ra toàn bộ bằng chứng cho phase: 13 ca biên của PRD, smoke hai tiến trình qua file kho, kiểm tất định từng byte, và ma trận AC → bằng chứng → đạt/chưa đạt để giảng viên đọc là tin.

**Blocked by:** None (viết test đỏ ngay; xanh sau khi 02–05 xong)

**Status:** ready-for-agent

- [ ] 13 ca biên của `docs/plan/phase-1-conformance.md` §6 có test hộp đen qua `headless_cmd`, chạy bằng một lệnh.
- [ ] Smoke hai tiến trình: `gather` 1 tick ở bến → file kho → `quan` tick 0 thấy đúng `stock`.
- [ ] Cùng seed chạy hai lần cho JSONL giống từng byte; tick dừng không phải bội số vẫn có snapshot cuối.
- [ ] Mã thoát 2 cho input/scenario sai và **không** tạo file đầu ra; mã 2 cho `day`, `river`, `--ticks -1`, cờ sai mode.
- [ ] `docs/verification/phase-1.md` điền đủ AC → cách kiểm → bằng chứng (file trong `docs/proof/phase-1/`) → đạt/chưa đạt, ghi trung thực phần chưa xong.
- [ ] `docs/proof/phase-1/` có lệnh đã chạy + output thật (ít nhất: smoke, tất định, một ca ngất, một ca hết kiên nhẫn).
