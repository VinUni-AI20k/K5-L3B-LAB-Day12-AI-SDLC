# tiepnnk01-10 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm:** QA lead, UI, lát 5 (`day`, Shop, pause).
  - P1: 33 test hộp đen, `run_checks.py`, HUD quán — [PR #5](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/pull/5).
  - P2: `--mode day`, Shop, pause — [PR #7](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/pull/7).
  - P3: test và HUD độ tươi, `day` bàn giao kho cá thể — [PR #11](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/pull/11), [#20](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/pull/20).
  - P4: 21 SVG, 24 SFX có phụ đề — [PR #22](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/pull/22); 3 cảnh báo, tương phản cao — [PR #26](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/pull/26).
- **Đã giúp ai:** báo lát 3, 4 bốn fixture quán sai vẫn trả mã 0 (AC-P1-29b); liệt kê 56 test cũ sẽ vỡ khi bật v1.2 kèm người đổi (AC-P3-19).
- **AI sai ở đâu:**
  - Test xanh vì lý do sai (kho rỗng): tôi chạy headless từng fixture.
  - Tương phản cao làm nhãn bếp thành cục đen, test không bắt: chỉ thấy khi nhìn ảnh chụp.
  - Làm trùng `verify-phase`, làm hộ lát 0 chưa báo: thấy khi xem nhánh nhóm.
- **Bài học:** test xanh chưa đủ, phải nhìn kết quả thật; kéo `main` và báo nhóm trước khi làm việc ngoài lát.
