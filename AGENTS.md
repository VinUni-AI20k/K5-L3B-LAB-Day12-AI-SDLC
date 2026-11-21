# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
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
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo cả nhóm (đổi hợp đồng ảnh hưởng mọi module).
- Không làm hỏng nhánh chính: trước khi đẩy, chạy test.
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO.
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi lý do đổi test trong commit.

## Quy tắc làm việc với agent
- Mỗi agent một việc rõ ràng (một lát). Cho agent đọc PRD/ticket đúng phase và hợp đồng kho trước.
- Agent làm xong phải chạy test và ghi kết quả vào mô tả commit hoặc `docs/proof/`; người đọc lại thay đổi trước khi đẩy.
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem README, mục "Tự do sáng tạo").

## Skills / hooks của nhóm
- `smoke-hai-tien-trinh` (`.agents/skills/smoke-hai-tien-trinh/`): smoke hộp đen v1.2 — ngưỡng ươn 30 (fixture TICKET-03), gather → file kho cá thể → quan, kho đếm / sai trả mã 2. Dùng trước khi gộp lát đụng sim/kho/runner và trước khi gắn tag.
  `python3 .agents/skills/smoke-hai-tien-trinh/smoke.py [--proof docs/proof/phase-n]`
- `kiem-tat-dinh` (`.agents/skills/kiem-tat-dinh/`): chạy headless 2 lần cùng seed, so JSONL + kho từng byte (gather, quan, nhiều seed). Dùng sau khi sửa luật có RNG, thứ tự duyệt, định dạng số, hoặc thêm phần sáng tạo.
  `python3 .agents/skills/kiem-tat-dinh/kiem_tat_dinh.py [--seeds 1 42 -7] [--ticks 3600] [--proof docs/proof/phase-n]`
- Hợp đồng tích hợp (kho, sự kiện, trạng thái quán chung lát 3–4): `docs/contracts/README.md`. Agent đọc file này trước khi sửa `sim/*`.
