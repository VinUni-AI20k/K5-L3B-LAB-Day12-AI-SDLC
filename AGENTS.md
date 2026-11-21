# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Contract 1.3 khai `bench_cmd` và `soak_cmd` ở gốc `game.contract.json`; bộ kiểm nối `--seed`, `--duration`, `--out` (bench) và `--seed`, `--days`, `--out` (soak)
- Bench: `python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json` (làm nóng 3 s, cảnh lặn 1280×720)
- Soak 10 Ngày: `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json` (thoát 1 nếu sim ném lỗi)
- Kiểm tất định: `python3 tools/check_determinism.py` (cùng seed, output giống từng byte)
- Smoke Phase 1 (hộp đen, 27 mục): `python3 tools/smoke_phase1.py`; Phase 2: `python3 tools/smoke_phase2.py` (cả hai chạy contract 1.1 sinh từ `game.contract.json`); Phase 3, contract 1.2 và kho cá thể: `python3 tools/smoke_phase3.py`
- Test hồi quy Phase 1-2 chạy headless với bản 1.1 (`run_headless` trong `tests/helpers.py`, biến `CHONOI_CONTRACT`); test 1.2 dùng `run_headless(..., v12=True)`.
- Headless: `python3 -m chonoi.headless --mode gather|quan --seed 1 --ticks 600 --out out.jsonl`
- Chơi thử trên trình duyệt: `python3 -m chonoi.live` (menu chính) hoặc `python3 -m chonoi.live --mode gather|quan|day [--days N]` (mở địa chỉ in ra; WASD, E, Space, P/Esc tạm dừng, R chơi lại, M về menu; Shop: 1 mua oxy, 2 mua Máu, Enter sang Ngày mới)

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
- **Skill `check-determinism`** (`.agents/skills/check-determinism/SKILL.md`, chạy `python3 tools/check_determinism.py`): chạy headless hai lần cùng seed rồi so từng byte. Dùng sau khi sửa luật trong `chonoi/sim/`, trước khi mở PR và trước khi gắn tag.
- **Skill `check-no-hardcode`** (`.agents/skills/check-no-hardcode/SKILL.md`, chạy `python3 tools/check_no_hardcode.py`): quét literal số trong `chonoi/sim/` đối chiếu tuning của `game.contract.json`. Dùng sau khi sửa luật trong `chonoi/sim/` và trước khi mở PR.
- **Hook `protect_locked_files`** (`.agents/hooks/protect_locked_files.py`, nối trong `.claude/settings.json`): hỏi lại người dùng trước khi agent sửa `game.contract.json`, `docs/contracts/` hay `chonoi/inventory.py` (schema kho). Chỉ đồng ý khi Integrator đã báo cả nhóm.
- Windows không có `python3` thì gõ `python`; hai công cụ trên tự dùng python đang chạy.
- **Hook `pre-push`** (`.agents/hooks/pre-push`, C): chạy toàn bộ test trước mỗi `git push`, test đỏ thì chặn. Cài một lần mỗi máy: `sh .agents/hooks/install.sh` (đặt `core.hooksPath`). Bỏ qua khẩn cấp: `git push --no-verify` và ghi lý do vào standup.
