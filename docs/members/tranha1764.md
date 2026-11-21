# tranha1764 — phản tư cá nhân (≤ 200 từ)

- Vai trò trong nhóm: Phụ trách `sim/gather` · Integrator ở Phase 1–3 · Release / Integrator ở Phase 4 · Dự phòng `sim/quan`.
- Tôi đã làm (kèm link commit): Tôi triển khai oxy và ngất ở [Phase 1](https://github.com/ngominhcuong/K5-L3B-LAB-Day12-AI-SDLC-4npc/commit/78f4345), cá bơi và sinh đàn ở [Phase 2](https://github.com/ngominhcuong/K5-L3B-LAB-Day12-AI-SDLC-4npc/commit/e4fc789), rồi kho cá thể và độ tươi ở [Phase 3](https://github.com/ngominhcuong/K5-L3B-LAB-Day12-AI-SDLC-4npc/commit/d1b7fde). Với vai Integrator, tôi chốt tag `phase-3`.
- Tôi đã review (kèm link): Tôi rà phần bàn giao kho trên [commit tích hợp Phase 3](https://github.com/ngominhcuong/K5-L3B-LAB-Day12-AI-SDLC-4npc/commit/39be0e1). Tôi hỗ trợ QA bằng cách chạy ca nối kho, phục vụ và thu tiền, rồi so hash hai lần chạy.
- AI sai ở đâu và tôi phát hiện thế nào: Bản mã Codex đề xuất còn giữ `kind` và thiếu `pos` trong payload `monster_hit` v1.1. Khi rà conflict, tôi đối chiếu với [bản sửa của QA](https://github.com/ngominhcuong/K5-L3B-LAB-Day12-AI-SDLC-4npc/commit/d4ce64e) để giữ `pos` cùng danh sách hàng rơi theo schema mới.
- Điều tôi học được: Kiểm trên đúng commit bàn giao và thử tới cuối vòng chơi. Quán nhận kho đúng ở tick 0 vẫn chưa đủ để kết luận Shop xử lý được hàng dư.
