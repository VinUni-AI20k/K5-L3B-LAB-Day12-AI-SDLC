# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Headless: `python3 -m chonoi.headless --mode day --days 1 --seed 42 --ticks 22200 --out tmp/day.jsonl` (tạo `tmp/` trước khi chạy).
- Chơi thử trên trình duyệt: `python3 -m chonoi.live --mode day` (mở địa chỉ in ra, dùng WASD, E, Space, P hoặc Esc).
- PowerShell: `$env:PYTHONPATH='tests;.'; $env:PYTHONUTF8='1'; .\.venv\Scripts\python.exe -B -m unittest discover -s tests -v`. Trên Windows, helper dùng chung chạy lệnh headless của starter với Python đang chạy test.

## Cấu trúc & quy ước
- (Starter Python là TÙY CHỌN; nhóm có thể dùng ngôn ngữ khác nếu giữ Test Contract.) Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa; nếu phải sửa thì báo cả nhóm và ghi lại lý do.
- Luật chơi của nhóm: `chonoi/sim/gather.py`, `chonoi/sim/quan.py` (tìm `TODO(nhóm)`).
- **Số liệu chỉ đọc từ `game.contract.json` / dữ liệu**, không hard-code trong luật.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.

## Nên tránh
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo cả nhóm (đổi hợp đồng ảnh hưởng mọi module).
- Không làm hỏng nhánh chính: trước khi đẩy, chạy test.
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO.
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi lý do đổi test trong commit.

## Quy tắc làm việc với agent
- Codex hỗ trợ gợi ý, soạn nháp và kiểm tra. Thành viên phụ trách tự review phần của mình. Khôi review và xác nhận nội dung dùng chung. Trong tài liệu, ghi đề xuất đang chờ review cho tới khi người phụ trách thực sự xác nhận.
- Mỗi agent một việc rõ ràng (một lát). Cho agent đọc PRD/ticket đúng phase và hợp đồng kho trước.
- Diên giữ `sim/gather.py`, Nhân giữ `sim/quan.py`, Khôi giữ HUD, manifest, runner và kiểm tích hợp. Thay đổi dùng chung báo Khôi trước.
- Phase 2 dùng giao diện trong `docs/contracts/phase-2.md`. Runner nối hai ca, giữ bộ đếm pause và bàn giao kho đếm qua file hoặc trong vòng `day`.
- Phase 3 chia phần theo `docs/plan/phase-3.md` và `docs/contracts/phase-3.md`. Diên giữ adapter kho và Gather, Nhân giữ Quán, Khôi giữ kết nối chung và HUD. Gộp Diên rồi Nhân với manifest v1.1. Khôi bật v1.2 trong PR cuối sau khi kiểm cả hai đầu.
- Đặt kit, fixture thử tay và output tạm dưới `tmp/`. Stage từng đường dẫn đã rà diff. Phần phụ thuộc chưa vào `main` thì ghi việc đang chờ và dừng tại đó.
- Agent làm xong phải chạy test và ghi kết quả vào mô tả commit hoặc `docs/proof/`; người đọc lại thay đổi trước khi đẩy.
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem README, mục "Tự do sáng tạo").

## Skills / hooks của nhóm
- (Ghi tên và khi nào dùng; tối thiểu 2 skill/hook/command nhóm tự viết, đặt ở `.agents/skills/` hoặc tương đương.)
