# Tiberu2611 — phản tư cá nhân (≤ 200 từ)

Vai thực tế: TV3 — `sim/quan` lát 4 và tích hợp gather → quan.

- Tôi đã làm (kèm link commit):
  - Bếp, chọn interact, nấu, bưng: [1ecca2e](https://github.com/nlamtung/K5-L3B-LAB-Day12-AI-SDLC-Nhom456/commit/1ecca2e)
  - Phục vụ, boa, trả tiền, uy tín, đóng ca: [1a8d67b](https://github.com/nlamtung/K5-L3B-LAB-Day12-AI-SDLC-Nhom456/commit/1a8d67b)
  - Test tích hợp gather → kho → quan + bằng chứng: [fa006b0](https://github.com/nlamtung/K5-L3B-LAB-Day12-AI-SDLC-Nhom456/commit/fa006b0), [a6950ad](https://github.com/nlamtung/K5-L3B-LAB-Day12-AI-SDLC-Nhom456/commit/a6950ad)
  - Gộp lát 3 với lát 4: [0b9a040](https://github.com/nlamtung/K5-L3B-LAB-Day12-AI-SDLC-Nhom456/commit/0b9a040) · [PR #4](https://github.com/nlamtung/K5-L3B-LAB-Day12-AI-SDLC-Nhom456/pull/4)
- Tôi đã review (kèm link): đọc nhánh `tv2` và `docs/contracts/quan.md` của TV2, kiểm tra conflict và độ tương thích với `TungNL` (93/93 test) trước khi mở PR #4.
- AI sai ở đâu và tôi phát hiện thế nào: AI viết test boa khi chưa có lát 3 nên lệch 1 tick kiên nhẫn; khi gộp nhánh AI sửa cả file của TV2. Tôi phát hiện khi chạy toàn bộ test và đọc diff, rồi yêu cầu sửa test theo PRD và hoàn tác phần ngoài phạm vi ([c2cdadd](https://github.com/nlamtung/K5-L3B-LAB-Day12-AI-SDLC-Nhom456/commit/c2cdadd)).
- Điều tôi học được: thống nhất hợp đồng dữ liệu (khách, payload món) trước giúp gộp code hai lát chỉ còn xử lý trùng hàm; luôn đọc diff trước khi push và giữ đúng phạm vi việc của mình.
