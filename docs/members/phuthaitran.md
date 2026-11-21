# phuthaitran — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit):
  + [90d9766](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/90d9766): fixture `tests/fixtures/quan_one_customer.json` để test lát 4 không chờ lát 3.
  + [9feefc4](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/9feefc4): `QuanSim.step` theo 5 bước PRD-0 F; chọn interact, nấu, bưng, phục vụ, boa, trả tiền, cuối ca.
  + [525ef5a](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/525ef5a): 26 test lát 4 (AC-P1-09, AC-P1-10).
  + [66fe221](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/66fe221), [14b55d7](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/14b55d7): chơi thử quán với kho thật, sửa nhanh payload và HUD, lưu bằng chứng ở `docs/proof/phase-1/quan-playtest/`.
- Tôi đã review (kèm link): chưa review PR lát 3 trên GitHub (PR #3 đã gộp trước). Khi tích hợp, tôi tìm ra payload `no_dish`/`customer_arrived` lệch PRD và validator crash với `dish` dạng object.
- AI sai ở đâu và tôi phát hiện thế nào: AI không đọc được PRD trên lab board nên tôi phải dán vào. Bản đầu của một test viết mâu thuẫn, phải viết lại. Tôi kiểm đột biến để chắc test bắt được lỗi luật.
- Điều tôi học được: chốt cấu trúc dữ liệu chung sớm giúp hai lát làm song song; khi hợp đồng nhóm lệch PRD thì theo PRD và báo PO.
