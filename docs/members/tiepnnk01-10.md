# tiepnnk01-10 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link):** QA lead, UI và lát 5 (`day`, Shop, pause).
  - P1: 33 test hộp đen, `tools/run_checks.py`, HUD quán — [PR #5](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/pull/5).
  - P2: `--mode day`, Shop nâng cấp, pause — [PR #7](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/pull/7).
  - P3: test độ tươi, HUD độ tươi, `day` bàn giao kho cá thể — [PR #11](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/pull/11), [PR #20](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/pull/20).
  - P4: 21 SVG và 24 SFX có phụ đề — [PR #22](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/pull/22); 3 cảnh báo và tương phản cao — [PR #26](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/pull/26).
- **Đã giúp ai:** báo lát 3 và 4 bốn fixture quán sai vẫn trả mã 0 (AC-P1-29b); liệt kê 56 test cũ sẽ vỡ khi bật v1.2 kèm người đổi (`docs/verification/phase-3.md`, AC-P3-19).
- **AI sai ở đâu, tôi phát hiện thế nào:**
  - Test xanh vì lý do sai (fixture bị từ chối do kho rỗng): tôi chạy headless từng fixture.
  - Tương phản cao làm nhãn bếp thành cục đen, test không bắt được: chỉ thấy khi nhìn ảnh chụp trình duyệt.
  - Viết trùng `verify-phase` và làm hộ lát 0 mà chưa báo: xem nhánh của nhóm sau khi xong.
- **Điều tôi học được:** test xanh chưa đủ, phải nhìn kết quả thật. Kéo `main` thường xuyên và báo nhóm trước khi làm việc ngoài lát.
