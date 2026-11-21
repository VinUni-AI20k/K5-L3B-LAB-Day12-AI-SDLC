# czx04 — phản tư cá nhân (≤ 200 từ)

Dư Văn Hùng · `qa` · QA lead, PO.

- Tôi đã làm (kèm link commit):
  - TEAM.md, thỏa thuận nhóm, team 6667, nhận PO: [01c982b](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/01c982bfbc69f1e4ff9179cbce805173e9453bdf), [1008631](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/1008631a516c827b4c042e65fcf24eed0c4a0b59), [337e456](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/337e45644788a7c455038c8c63f0a9630d39a691)
  - Contracts + clarify theo PRD-0: [bfb3f3c](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/bfb3f3c913a548a5451980aea54c85004355b947), [8c1b494](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/8c1b494118ce7662306da9225752f8c50db5b58d)
  - Test gather/quan, smoke: [5790001](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/5790001cf64bb78209427d5365339ebd3a679a74), [b0822f7](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/b0822f7a0184b7a453464f8c7e4d85c66e987805), [0616d53](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/0616d53bbe25a1ced1a2279d980158f9ec1ab4eb)
  - README, ma trận truy vết, kiểm tay HUD: [640011c](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/640011c3db992e4c88d54d21f054a31013e3e9b9), [995080f](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/995080f), PR [#7](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/pull/7)
- Tôi đã review (kèm link): [#3](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/pull/3), [#4](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/pull/4) bằng Codex + gộp thử chạy test; tìm 2 lỗi chặn ở #3 (`tip: 0` bị mã 2, `dish_id: []` crash), Nam sửa ở 35b237f.
- AI sai ở đâu và tôi phát hiện thế nào:
  - Contracts nháp viết trước khi PRD mở đoán sai `data` sự kiện; đối chiếu PRD-0 mục E thì lộ ra.
  - Codex gợi ý giỏ thêm `node_yield` món; đọc lại PRD F: "thêm 1 nguyên liệu".
- Điều tôi học được: hợp đồng chỉ coi là chốt sau khi đối chiếu PRD; ghi rõ chỗ nào còn giả định. Viết test hộp đen trước rồi bật dần theo lát giúp bắt lỗi tích hợp sớm. Kết quả AI phải chạy lại và đọc lại PRD trước khi tin.
