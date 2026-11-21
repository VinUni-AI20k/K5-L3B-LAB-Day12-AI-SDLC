# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
- Smoke + bằng chứng phase 3: `tools/smoke_p3.sh` (v1.2: ngưỡng spoiled, bàn giao kho cá thể, kho đếm → mã 2, day, tất định, regression).
- Smoke + bằng chứng phase 2: `tools/smoke_p2.sh` (regression, bàn giao kho, day tất định, nâng cấp ngày kế).
- Vòng ngày: `python3 -m chonoi.headless --mode day --days 5 --seed 1 --ticks 111000 --out out.jsonl`
- Chơi đầy đủ: `python3 -m chonoi.live --mode day` (Esc/P pause, Shop mua bằng nút).
- Smoke + bằng chứng phase 1: `tools/smoke_p1.sh`
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Headless: `python3 -m chonoi.headless --mode gather|quan --seed 1 --ticks 600 --out out.jsonl`
- Chơi thử trên trình duyệt: `python3 -m chonoi.live --mode gather|quan` (mở địa chỉ in ra; WASD, E, Space, R)

## Cấu trúc & quy ước
- (Starter Python là TÙY CHỌN; nhóm có thể dùng ngôn ngữ khác nếu giữ Test Contract.) Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa; nếu phải sửa thì báo cả nhóm và ghi lại lý do.
- Luật chơi của nhóm: `chonoi/sim/gather.py`, `chonoi/sim/quan.py` (tìm `TODO(nhóm)`).
- **Số liệu chỉ đọc từ `game.contract.json` / dữ liệu**, không hard-code trong luật.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.

## Nên tránh
- **Mỗi người chỉ sửa file mình giữ** (bảng phân file trong `docs/plan/phase-<n>.md`). File dùng chung (`chonoi/jsonl.py`, `game.contract.json`, `chonoi/inventory.py`, `docs/*.md` của người khác) thì báo kênh nhóm trước, một người sửa, người kia rebase. Lý do: P3 hai PR cùng sửa `jsonl.py` → gộp ra `NameError`, 121 test đỏ; merge P2 đè ghi chép P1.
- Trước khi merge `dev` → `main`: `git diff main dev -- docs/` để không đè ghi chép.
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo cả nhóm (đổi hợp đồng ảnh hưởng mọi module).
- Không làm hỏng nhánh chính: trước khi đẩy, chạy test.
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO.
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi lý do đổi test trong commit.

## Quy tắc làm việc với agent
- Mỗi agent một việc rõ ràng (một lát). Cho agent đọc PRD/ticket đúng phase và hợp đồng kho trước.
- Agent làm xong phải chạy test và ghi kết quả vào mô tả commit hoặc `docs/proof/`; người đọc lại thay đổi trước khi đẩy.
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem README, mục "Tự do sáng tạo").

## Skills / hooks của nhóm
- Command `tools/smoke_p1.sh`: kiểm bàn giao kho và regression phase 1.
- Command `tools/smoke_p2.sh`: kiểm vòng ngày, Shop, cấp active và JSONL tất định trước PR/tag phase 2.
- Nguồn Phase 2: `docs/tickets/TICKET-02.md`; thay contract/khung phải ghi lý do trong `docs/verification/phase-2.md`.
