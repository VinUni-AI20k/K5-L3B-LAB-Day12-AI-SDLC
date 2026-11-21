# nhaipt342k4 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - Module `client/ui`: HUD 2 buổi theo PRD-0 (`d853e11`).
  - Mở rộng #1 "Lời Má Tư", thoại giọng Nam Bộ chỉ chạy ở client (`c14a6ce`).
  - Vẽ lại cá và bông (`2fd2a51`); dùng ảnh public domain cho cá và đáy sông, có ghi CREDITS (`a6afa97`).
  - Gộp lát 3 và 4 rồi sửa gợi ý quán (`810617c`, `640d03e`).
  - Bằng chứng: `docs/proof/phase-1/ui/`, `mo-rong-1-headless.txt`.
- **Tôi đã review (kèm link):** *(điền sau khi duyệt PR của bạn khác)*
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI chạy test bằng `python3` trên Windows, báo 20 lỗi giả; đọc log thì thấy lỗi do môi trường, không phải do code.
  - AI tự thêm dòng đồng tác giả Claude vào commit; tôi thấy trên GitHub và yêu cầu bỏ.
  - Ảnh chụp "đang nấu" hiện khách "đang ăn" do snapshot dính tham chiếu; tôi so với số in ra thì thấy.
  - Chạy số thật mới lộ gợi ý sai lúc đang bưng món.
- **Điều tôi học được:** UI chỉ đọc snapshot thì sáng tạo thoải mái mà không phá headless; chốt tên trường sớm giúp HUD khớp ngay khi gộp.
