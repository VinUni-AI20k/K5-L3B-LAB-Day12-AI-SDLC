# trinhtuanphong123 — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit):
  - Lát 1 `gather` (oxy, ngạt, ngất): [`eb4885d`](https://github.com/mKhaiTruong/K5-L3B-LAB-Day12-AI-SDLC-G2026/commit/eb4885d), [`d71607f`](https://github.com/mKhaiTruong/K5-L3B-LAB-Day12-AI-SDLC-G2026/commit/d71607f), PR [#4](https://github.com/mKhaiTruong/K5-L3B-LAB-Day12-AI-SDLC-G2026/pull/4).
  - Lát 2 `gather` (hái, bắt cá): [`a9f2305`](https://github.com/mKhaiTruong/K5-L3B-LAB-Day12-AI-SDLC-G2026/commit/a9f2305), [`72271b0`](https://github.com/mKhaiTruong/K5-L3B-LAB-Day12-AI-SDLC-G2026/commit/72271b0), PR [#7](https://github.com/mKhaiTruong/K5-L3B-LAB-Day12-AI-SDLC-G2026/pull/7).
  - README [`045a046`](https://github.com/mKhaiTruong/K5-L3B-LAB-Day12-AI-SDLC-G2026/commit/045a046); bằng chứng `docs/proof/phase-1/` (smoke, chơi thật, tất định, ảnh HUD).
- Tôi đã review (kèm link):
  - PR [#8](https://github.com/mKhaiTruong/K5-L3B-LAB-Day12-AI-SDLC-G2026/pull/8) của Khuê: ghép thử với `main` và nhánh README, không xung đột, 88 test xanh; đã comment.
- AI sai ở đâu và tôi phát hiện thế nào:
  - Spec ghi sai số dòng import và để sót docstring cũ sau task 01. Phát hiện khi rà spec và đọc diff trước commit.
  - HUD tối do khung vẽ: kho chưa trừ phần giữ chỗ, nhãn bếp hiện `[object Object]`. Phát hiện khi chơi thử.
- Điều tôi học được:
  - Spec nhỏ có số tham chiếu đã chạy thử (ngạt t+59, hồi chiêu mở ở bước 30) giúp Sonnet code đúng ngay.
  - Test xanh chưa đủ; phải chơi thật và kiểm tất định.
