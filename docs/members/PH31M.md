# PH31M — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit):
  - Scrum Lead: điều phối tiến độ, cổng kiểm, tag `phase-1`, quản trị repo.
  - Lát 4 Quán service (Ticket 05 P1): nấu nướng, phục vụ, boa, tính tiền, đóng ca ([49c28e7](https://github.com/PH31M/K5-L3B-LAB-Day12-AI-SDLC-MMMMV/commit/49c28e7), [ce3e0df](https://github.com/PH31M/K5-L3B-LAB-Day12-AI-SDLC-MMMMV/commit/ce3e0df)).
  - Ticket 04 P2: mở rộng 2 bếp song song, 4 bàn, 6 món (+cá kèo, kèo nèo), lọc theo `day_plan.dishes` ([e0bd7cd](https://github.com/PH31M/K5-L3B-LAB-Day12-AI-SDLC-MMMMV/commit/e0bd7cd)).
  - Viết 20 unit test (`test_quan_service.py`, `test_quan_p2.py`), cập nhật `AGENTS.md`, `CHANGELOG.md`, ma trận Phase 2.
- Tôi đã review (kèm link):
  - Review và merge PR #1 của Cao Minh (`feat/cao-minh`) module Gather Core ([9342f9e](https://github.com/PH31M/K5-L3B-LAB-Day12-AI-SDLC-MMMMV/commit/9342f9e)).
- AI sai ở đâu và tôi phát hiện thế nào:
  - AI tăng `ready_ticks` ngay tick món chín; tôi đối soát PRD và sửa dùng `stoves_ready_at_start` để chỉ tăng từ tick kế tiếp.
  - AI nhầm `day_plan` là trần bán; tôi sửa để khách tiếp tục gọi món nếu còn nguyên liệu.
- Điều tôi học được:
  - Kỹ năng chia lát độc lập (vertical slicing), bảo vệ Test Contract và dùng test biên kiểm soát AI thay vì tin tưởng mù quáng.
