
=======
Lê Quý Toàn · module `sim/gather` · vai `Integrator`

- Tôi đã làm (kèm link commit):
  - Lõi Buổi sáng (`sim/gather.py`: bơi, lặn, oxy, ngạt, ngất, giỏ, hái rau, bắt cá, cập bến, xuất kho) và test: [3e966f5](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/3e966f5)
  - Khóa hợp đồng Phase 1 tại `docs/contracts/` và kế hoạch: [d87b015](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/d87b015)
  - Sửa hồi chiêu khi giỏ đầy theo clarify #5, bật test gather: [28cf1a4](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/28cf1a4)
  - Sửa thêm giỏ theo `node_yield` từ config: [e7a34ae](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/e7a34ae)
  - PR gộp vào `dev`: [#4](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/pull/4), [#6](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/pull/6)
- Tôi đã review (xem trực tiếp, trao đổi miệng): [#3](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/pull/3) `sim/quan` (đối chiếu file kho), [#5](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/pull/5) `client/ui` (snapshot gather).
- AI sai ở đâu và tôi phát hiện thế nào:
  - AI gán cooldown 30 tick khi bắt cá hụt do đầy giỏ, trái clarify #5. Phát hiện khi chạy test gather.
  - AI hardcode thêm 1 món thay vì biến `node_yield`. Phát hiện qua review của trưởng nhóm tại PR #4.
- Điều tôi học được: Bám sát clarify, không để AI tự đặt luật ngầm; làm đúng lát cắt, không lấn module bạn khác; chuẩn hóa file kho giúp ghép 2 tiến trình chạy mượt.
>>>>>>> origin/dev
