# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Headless: `python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out.jsonl` (đổi `gather` thành `quan` để thử quán).
- Chơi thử trên trình duyệt: `python3 -m chonoi.live --mode gather` (hoặc `--mode quan`; mở địa chỉ in ra. Phím WASD, E, Space, R).
- Trên PowerShell, dùng `$env:PYTHONPATH = 'tests;.'` rồi chạy lệnh unittest. Kiểm tra `python3 --version` trước vì `headless_cmd` gọi `python3` trong tiến trình con.

## Cấu trúc & quy ước
- (Starter Python là TÙY CHỌN; nhóm có thể dùng ngôn ngữ khác nếu giữ Test Contract.) Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa; nếu phải sửa thì báo cả nhóm và ghi lại lý do.
- Phase 1 chia luật theo lát, từ `chonoi/sim/gather.py` (oxy, Máu, giỏ) và `chonoi/sim/gather_harvest.py` (hái, bắt cá) đến `chonoi/sim/quan_customers.py` (khách), `chonoi/sim/quan_service.py` và `chonoi/sim/quan.py` (bếp, phục vụ).
- Trước khi sửa, đọc kế hoạch và hợp đồng tích hợp. Sau khi chạy test, đối chiếu với ma trận. [Kế hoạch Phase 1](docs/plan/phase-1.md), [hợp đồng tích hợp](docs/contracts/README.md), [ma trận kiểm chứng](docs/verification/phase-1.md)
- **Số liệu chỉ đọc từ `game.contract.json` / dữ liệu**, không hard-code trong luật.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.

## Nên tránh
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo cả nhóm (đổi hợp đồng ảnh hưởng mọi module).
- Không làm hỏng nhánh chính: trước khi đẩy, chạy test.
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO.
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi lý do đổi test trong commit.

## Quy tắc làm việc với agent
- Mỗi agent một việc rõ ràng (một lát). Cho agent đọc PRD/ticket đúng phase và hợp đồng kho trước.
- Agent làm xong phải chạy test và ghi kết quả vào mô tả commit hoặc `docs/proof/`; người đọc lại thay đổi trước khi đẩy.
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem README, mục "Tự do sáng tạo").

## Skills / hooks của nhóm

- `python3 tools/phase_evidence.py tests --out playground/phase-1/unittest.txt` chạy unittest và lưu toàn bộ log để review PR hoặc cập nhật ma trận.
- `python3 tools/phase_evidence.py headless --out playground/phase-1/headless.txt` chạy hai lượt mỗi mode cùng seed, so từng byte và lưu SHA-256. Dùng trước khi Lead gắn tag.
- Sau khi thống nhất commit kiểm chứng, đưa bằng chứng vào `docs/proof/phase-1/` và ghi commit tương ứng trong ma trận.
