# ttkien0710 — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit):
  - Cài đặt toàn bộ logic Quán Lát 4 trong `chonoi/sim/quan.py`: bếp nấu, bưng bê, phục vụ bàn, thanh toán, tính tip 20% và cộng điểm uy tín (+0.2), kết thúc ca ([commit 4af1051](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/4af1051), [commit dcf6694](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/dcf6694), [commit 5d77733](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/5d77733)).
  - Viết suite 7 unit tests độc lập `tests/test_p1_quan_lat4.py`, xuất proof xác nhận 100% đạt.
  - Giải quyết xung đột 3 files với Lát 3 Quán và Lát Gather, đồng bộ tài liệu kiểm chứng ([commit 4767e84](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/4767e84)), mở [PR #3](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/pull/3) đã được gộp vào `main`.
- Tôi đã review (kèm link):
  - Review và đối chiếu logic nhận khách/giữ nguyên liệu Lát 3 Quán ([commit 7af1a49](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/7af1a49)) của Quoosc để đảm bảo tương thích 100% với logic phục vụ.
- AI sai ở đâu và tôi phát hiện thế nào:
  - Khi viết test tương tác, AI mô phỏng giữ phím `interact` liên tục mà không nhả phím giữa 2 lần bấm, dẫn đến `pressed("interact")` không bắt được cạnh lên. Tôi phát hiện qua `AssertionError: 0 != 1` và yêu cầu bổ sung `li.set(interact=False)`.
- Điều tôi học được:
  - Hiểu sâu về xử lý sự kiện cạnh lên (edge-triggered inputs), tầm quan trọng của việc kiểm thử độc lập bằng scenario/fixture và kỹ năng giải quyết conflict bảo vệ mã nguồn chung.
