# hungdt31: phản tư cá nhân (≤ 200 từ)

**Vai:** QA Lead (test, smoke, verification) · dự phòng `client/ui`.

**Tôi đã làm**
- P1: ma trận AC và smoke e2e nối kho (`d447e73`, `57bf3fe`); skill `qa-verify-phase`.
- P2: bot `tools/qa_autoplay.py`, smoke `day` 5 Ngày (`0ee6ed4`); sửa payload `monster_hit` (`d4ce64e`).
- P3: chuyển 20 test sang kho cá thể (`8da292b`); sửa 2 crash (`760cb34`) và lỗi id `I1` lặp mỗi Ngày (`32883d0`); viết CHANGELOG.
- P4: `soak_cmd` (`00d3e4c`), verification phase-4, kịch bản demo.

**Đã giúp:** sửa trong lát của `ngthanhtamtb` (`monster_hit`), `danhhieu204ns`, `ngominhcuong` (crash), `tranha1764` (id); báo nhóm về các tag trỏ vào commit đỏ.

**AI sai ở đâu:**
- Viết test id xuyên Ngày vẫn xanh trên code lỗi. Tôi chạy lại test trên code chưa sửa thì phát hiện.
- Muốn sửa assert cho khớp code khi chưa có ticket; tôi dừng lại và ghi clarify #6.
- Thử đo bench bằng Firefox snap thì để sót một tiến trình.

**Bài học:**
- Kiểm đúng commit sẽ gắn tag.
- Test hồi quy phải thấy đỏ trước rồi mới xanh.
- Đổi schema thì chạy toàn bộ test trong cùng PR.
