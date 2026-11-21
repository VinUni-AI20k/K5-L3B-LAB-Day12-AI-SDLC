# tiepnnk01-10 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):** QA lead + HUD + skill, nhánh `feat/qa`.
  - [`f164039`](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/commit/f164039), [`a0e460b`](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/commit/a0e460b): 33 test hộp đen theo AC PRD-0, cơ chế `@pending` để `main` luôn xanh.
  - [`78dff13`](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/commit/78dff13): HUD quán (kho khả dụng, trạng thái bếp, kiên nhẫn, món trên tay).
  - [`81a76cb`](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/commit/81a76cb), [`0fe2a35`](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/commit/0fe2a35): `tools/run_checks.py`, skill `run-checks`.
  - [`00d5862`](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/commit/00d5862): ma trận `docs/verification/phase-1.md`.
- **Tôi đã review (kèm link):** chạy test lát 1–3 sau khi merge `main` ([`1776060`](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/commit/1776060)): lát 1–3 đúng PRD; phát hiện 4 fixture quán mâu thuẫn vẫn trả mã 0 (AC-P1-29b), đã báo lát 3/4.
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - Một test fixture xanh vì lý do sai (bị từ chối do kho rỗng, không phải do tay/đơn lệch). Tôi chạy headless trực tiếp từng fixture thì thấy.
  - AI viết `run_checks.py` trùng `verify-phase` của nhóm vì không xem nhánh khác trước.
- **Điều tôi học được:** test xanh chưa chắc đúng; mỗi fixture chỉ nên sai một điều. Nên kéo `main` thường xuyên để tránh làm trùng.
