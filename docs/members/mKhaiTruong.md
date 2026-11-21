# mKhaiTruong — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit):
  - Setup nhóm, phân việc theo file, kế hoạch P1: [`c4d3eba`](https://github.com/mKhaiTruong/K5-L3B-LAB-Day12-AI-SDLC-G2026/commit/c4d3eba), [`f719473`](https://github.com/mKhaiTruong/K5-L3B-LAB-Day12-AI-SDLC-G2026/commit/f719473) (PR #1)
  - Hợp đồng kho, giao diện sim↔UI, bảng sự kiện: [`75a381c`](https://github.com/mKhaiTruong/K5-L3B-LAB-Day12-AI-SDLC-G2026/commit/75a381c) (PR #2)
  - `scenario.py` mã 2, gather: [`f9eead0`](https://github.com/mKhaiTruong/K5-L3B-LAB-Day12-AI-SDLC-G2026/commit/f9eead0) (PR #6); quan + giữ quá tồn: [`3b445e5`](https://github.com/mKhaiTruong/K5-L3B-LAB-Day12-AI-SDLC-G2026/commit/3b445e5) (PR #8)
  - Proof + ma trận verification Phase 1, gắn tag `phase-1` (Integrator)
- Tôi đã review (kèm link):
  - PR #3 (quan lát 3+4, Khánh), #4 và #7 (gather lát 1, 2, Phong), #5, #9, #10 (docs): gộp thử trong worktree tạm, chạy toàn bộ test trước khi merge
- AI sai ở đâu và tôi phát hiện thế nào:
  - (tự viết bằng lời của mình. Gợi ý có thật: fixture `tests/test_quan.py:170` giữ chỗ quá tồn, lộ ra khi thêm kiểm mới; bản nháp kiểm quan có `KeyError` khi thiếu `hand`)
- Điều tôi học được:
  - (tự viết)
