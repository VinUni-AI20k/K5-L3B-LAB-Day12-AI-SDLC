# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| Phase 1 | Nguyễn Như Duy An (`K0heii` — M6) | Xong `M6.1`–`M6.3` (`TEAM.md`, `contracts`, `scenario.py` + test), chuẩn bị sẵn `verification/phase-1.md`, `README.md`, `test_integration_m6.py` | Chờ M1–M5 merge để chạy `M6.4`–`M6.6` và gắn tag `phase-1` | Không |
| Phase 1 | Nguyễn Nhật Minh (`NhMinh-2610` — M4) | Xong `M4.1`–`M4.4` (spec/AC, 12 test M4 + ghép `CustomerMixin` của M3 vào `quan.py`, toàn bộ test M3 + M4 + M6 xanh) | Review chéo C ↔ D, hỗ trợ M6 chốt `verification/phase-1.md` | Không |
| 1 | Vũ Quang Huy (M1) | Hoàn thành M1.1–M1.4, 42 test đạt, lưu [bằng chứng M1](proof/phase-1/m1.md) | Review chéo với B và chuyển bằng chứng cho F | Không |
| Phase 1 | Vũ Quang Thanh (`thanhvu101` — M5) | Hoàn thành `M5.1`–`M5.4` (`AGENTS.md`, 2 skills, `docs/ui-contract.md`, HUD `gather`/`quan` trên `chonoi.live`, thêm `gather_bg.png` và lưu bằng chứng [m5.md](proof/phase-1/m5.md)) | Review chéo M5 ↔ M6, hỗ trợ đóng gói tag `phase-1` | Không |
| Phase 1 | Phùng Văn Thanh Cao (`ththanh8888` — M3) | Xong `M3.1`–`M3.4` (spec/AC, 18 test khách, `quan_customers.py`, test ghép M3 ↔ M4, bằng chứng `proof/phase-1/m3.md`); đã review chéo code M4 của Minh | Hoàn thiện hồ sơ cá nhân, hỗ trợ M6 duyệt bằng chứng, nhận việc dự phòng nếu nhóm cần | Chưa thấy bàn giao M2 (gather lát 2) nên chưa chạy được smoke gather → quán bằng kho thật |
| Phase 2 | Nguyễn Nhật Minh (`NhMinh-2610` — M4) | Hoàn thành `P2-M4.1`–`P2-M4.4` (`spec-p2-m4.md`, `shop.py`, `day.py`, Pause trong `runner.py`, test CLI hộp đen `--mode day --days 1|2` & Pause 3 mode, fix regression `test_quan_m4.py` theo v1.1, lưu `docs/proof/phase-2/m4-test-log.txt`) | Chờ `M3.3` (Cao) & `M1.3` (Huy) để chạy kiểm chứng tích hợp cuối Phase 2 | Không |
