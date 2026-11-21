# HoangHongNgo — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit): chốt hợp đồng kho/event/sim↔UI (`docs/contracts/README.md`); kiểm dải hợp lệ tuning trong `chonoi/contract.py` + `tests/test_p1_contract.py` (ea8e866); chia việc Phase 2 thành 6 lát song song (202d2a1); gộp main và chạy smoke hai tiến trình seed 42, so `cmp` hai lần.
- Tôi đã review (kèm link): PR lát 1, 2, 3, HUD và docs (HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi#1–#5).
- AI sai ở đâu và tôi phát hiện thế nào: khi chạy suite trên Windows, AI ban đầu coi 77 lỗi là lỗi luật; đọc mã thoát 9009 mới thấy là `python3` gọi nhầm stub Store, không phải sim sai.
- Điều tôi học được: chốt hợp đồng trước giúp các lát làm song song mà ít xung đột; cần ghi rõ cách chạy test cho từng hệ điều hành.
