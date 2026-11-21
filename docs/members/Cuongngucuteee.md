# Cuongngucuteee — phản tư cá nhân (≤ 200 từ)

**Thành viên C — Phan Trần Mạnh Cường.** Module: `client/ui`. Vai: Dev UI, Scrum.

- Tôi đã làm (kèm link commit):
  - Hook pre-push chạy test (HX-04): [`1a5799c`](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/commit/1a5799c)
  - P2-04 Cá Sấu, Máu, ngạt: [PR #30](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/30), [`733cee0`](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/commit/733cee0), [`d0bf701`](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/commit/d0bf701)
  - P2-08 menu, pause, HUD, Shop: [PR #35](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/35), [`50a096e`](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/commit/50a096e), [`bd3c714`](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/commit/bd3c714)
  - P4-05 đóng gói (README 3 lệnh, LICENSE, CHANGELOG, CREDITS, CI): nhánh `c/p4-05-packaging`
- Tôi đã review (kèm link): chưa review PR của người khác; PR của tôi được D review ([PR #30](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/30)).
- AI sai ở đâu và tôi phát hiện thế nào: test "đang ở mặt nước thì Cá Sấu không đuổi" chỉ kiểm tick cuối nên bỏ điều kiện vẫn xanh; D phát hiện khi phá thử, sửa thành kiểm từng tick. Lệnh mua thứ hai trong cùng tick ghi đè lệnh trước; lộ ra khi chụp màn Shop thật.
- Điều tôi học được: test phải được phá thử mới đáng tin; kiểm bằng mắt trên trình duyệt thật bắt được lỗi mà unit test bỏ qua; sheet và kế hoạch lệch mã việc thì đọc kế hoạch.
