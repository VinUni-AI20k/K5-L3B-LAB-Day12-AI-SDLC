# nganhduong123 — phản tư cá nhân (≤ 200 từ)

> Nháp giữa buổi (sau Phase 2). Cập nhật lại ở Phase 4.

- Tôi đã làm (kèm link commit):
  - Vai PO: TEAM.md, phân vai 7 người, `team_size = 7` ([8bc3a7f](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/8bc3a7f)); `docs/clarify.md` #1–#4; kế hoạch chia việc P1–P4 ([345bc97](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/345bc97), [44ab52d](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/44ab52d)).
  - Client web Ticket-02: menu, intro, pause, Shop, HUD ([eaf635a](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/eaf635a)); vẽ lại cảnh lặn và quán ([e9780b8](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/e9780b8)).
  - Hợp đồng tích hợp `docs/contracts/` ([bfb5160](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/bfb5160)). Nối client với `day.py` thật, sửa pause/`--days`/HUD quán, test `test_p2_ui_live.py`, bằng chứng `docs/proof/phase-2/ui-day/`. Chốt clarify #4–#6, #10–#15.
  - Harness AI: 2 skill trong `.agents/skills/` và script kiểm chứng tự xử lý `python3` trên Windows ([d506d1b](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/d506d1b)).
- Tôi đã review (kèm link):
  - Chưa có review ghi trên GitHub. Tôi tự gộp PR #2 và #5 của mình. Từ Phase 3 tôi sẽ review PR của invzble-z (người tôi dự phòng).
- AI sai ở đâu và tôi phát hiện thế nào:
  - AI ghi "đã gắn tag `phase-1`" mà không kiểm. Tôi chạy `git ls-remote --tags origin`, thấy rỗng nên sửa lại.
  - AI đề xuất lưu độ tươi bằng 240 đơn vị/điểm. Khi rà lại thấy cách này chỉ đúng với fixture là bội của 1/240 (`33.33 × 240 = 7999.2`, không nguyên), nên kế hoạch Phase 3 đổi sang `Fraction`.
- Điều tôi học được:
  - _(Tự điền: 1–2 câu bằng lời của bạn.)_
