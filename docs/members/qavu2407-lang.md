# qavu2407-lang — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - Lát 2 gather: hái nút, mọc lại, bắt cá, hồi chiêu, báo giỏ đầy ([699162a](https://github.com/Ama2352/K5-L3B-LAB-Day12-AI-SDLC-Banana/commit/699162a)), kèm 11 test hộp đen ([1747382](https://github.com/Ama2352/K5-L3B-LAB-Day12-AI-SDLC-Banana/commit/1747382)).
  - Lệnh và skill kiểm bàn giao kho gather → quan ([dee3574](https://github.com/Ama2352/K5-L3B-LAB-Day12-AI-SDLC-Banana/commit/dee3574)).
  - Một lượt thu nguyên liệu thật, file kho và ma trận truy vết phase 1 ([70e62ee](https://github.com/Ama2352/K5-L3B-LAB-Day12-AI-SDLC-Banana/commit/70e62ee), [f8e898f](https://github.com/Ama2352/K5-L3B-LAB-Day12-AI-SDLC-Banana/commit/f8e898f), [fc28c66](https://github.com/Ama2352/K5-L3B-LAB-Day12-AI-SDLC-Banana/commit/fc28c66)).
  - Hợp đồng file kho, giao diện sim ↔ UI và bảng sự kiện trong `docs/contracts/README.md`.
- **Tôi đã review (kèm link):** chưa review PR nào trong phase 1. Đã gộp thử nhánh lát 3 (`NguyenNgocVinh`) với nhánh của tôi: không xung đột, test xanh.
- **AI sai ở đâu và tôi phát hiện thế nào:** dựng sai fixture test (cá ở d = 0.5 vẫn là mặt nước), lộ ra khi test đỏ. Quên `.gitignore` chặn `*.jsonl` nên thiếu file bằng chứng, lộ ra khi kiểm trên bản checkout sạch.
- **Điều tôi học được:** cho AI đọc đúng PRD trước khi code thì luật ra đúng ngay, chỗ hay sai là dữ liệu test. Bằng chứng phải kiểm trên bản clone sạch, không phải trên máy mình.

## Phase 2 (≤ 200 từ)

- **Tôi đã làm (kèm link commit):** *(chưa commit, sẽ thêm link sau khi đẩy nhánh `VuNgocQuynhAnh`)*
  - Gather v1.1 (`chonoi/sim/gather.py`): cá kèo, kèo nèo N5/N6, 8 đàn đầu ca, cá bơi/đổi hướng/phản xạ mép, sinh cá 360·k (trần 12); bắt trước khi cá bơi.
  - Kiểm dữ liệu cá ở `contract.py`, `scenario.py`; `check_handoff` đọc 6 loại từ contract.
  - 20 test hộp đen `tests/test_gather_p2.py`; smoke kho tích hợp `docs/proof/phase-2/`; 4 giả định trong `docs/clarify.md`.
- **Tôi đã review (kèm link):** gộp thử nhánh Phase 2 của `AnhQuanHANU` với nhánh của tôi: không xung đột, 71/71 test xanh, `check_handoff` khớp.
- **AI sai ở đâu và tôi phát hiện thế nào:** AI ghi vào hợp đồng kho rằng mode `day` đã tự bàn giao, nhưng chạy `--mode day` vẫn thoát mã 2; tôi phát hiện khi chạy thử lệnh lúc rà soát. Test so byte mở file không đóng, lộ ra qua ResourceWarning.
- **Điều tôi học được:** tài liệu cũng phải chạy thử như code: mỗi câu "đã có" trong hợp đồng cần một lệnh chứng minh. Rà soát cả module mới thấy lát 1 gather còn TODO.
