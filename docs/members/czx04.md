# czx04 — phản tư cá nhân (≤ 200 từ)

Dư Văn Hùng · `qa` · QA lead, PO.

- Tôi đã làm (kèm link commit):
  - Nhận PO ([337e456](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/337e45644788a7c455038c8c63f0a9630d39a691))
  - README nhóm ([640011c](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/640011c3db992e4c88d54d21f054a31013e3e9b9))
  - Bật test quan ([0616d53](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/0616d53bbe25a1ced1a2279d980158f9ec1ab4eb))
  - Clarify #12/#13 ([8c1b494](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/8c1b494118ce7662306da9225752f8c50db5b58d))
  - Test quan, smoke ([b0822f7](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/b0822f7a0184b7a453464f8c7e4d85c66e987805))
  - Sửa test gather ([5790001](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/5790001cf64bb78209427d5365339ebd3a679a74))
  - Sửa contracts/clarify ([bfb3f3c](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/bfb3f3c913a548a5451980aea54c85004355b947))
  - Đặt team 6667 ([1008631](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/1008631a516c827b4c042e65fcf24eed0c4a0b59))
  - Sửa test_team_check ([2464506](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/246450666d9b1298c3b90ef07b1e86f3bc2e0d42))
  - Khung test gather ([a554654](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/a55465466e8b54d3475472f66899ea354ebbabd8))
  - Cập nhật TEAM ([7854f22](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/7854f22e75e27a56d763a902c367afc0fbd97b22))
  - Thỏa thuận nhóm ([01c982b](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/01c982bfbc69f1e4ff9179cbce805173e9453bdf))
  - Contracts/clarify ban đầu ([7d6393a](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/7d6393adc0bf014546e46413b2692e5035fad348))
- Tôi đã review (kèm link): [#3](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/pull/3) (quan), [#4](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/pull/4) (gather), bằng Codex CLI; gộp thử 3 nhánh chạy test. #3: khách chưa phục vụ có `tip: 0` → mã 2; `dish_id: []` crash mã 1. Nam sửa: 35b237f.
- AI sai ở đâu và tôi phát hiện thế nào:
  - Claude soạn contracts trước khi mở PRD: gather thiếu amount; fish_caught dùng count thay yield; hold_full sai khóa; data quan sai. Đối chiếu PRD-0 E, sửa bfb3f3c.
  - Codex gợi ý giỏ thêm node_yield món; đọc lại PRD F: “thêm 1 nguyên liệu”.
  - Claude nhầm clarify #12/#13 do Codex thêm; thực tế PO thêm.
- Điều tôi học được: TODO(czx04): tự viết
