# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.
> Trạng thái: Release `v1.0.0` (Phase 4, Test Contract v1.3). Tag `phase-1`…`phase-4` đã đẩy.

## Lệnh
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
  (Windows PowerShell: `$env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v`)
- Headless: `python3 -m chonoi.headless --mode gather|quan|day --seed 1 --ticks 600 --out out.jsonl`
  (`--days 1..5` chỉ với `day`; một Ngày đủ = `--ticks 22200`, phải chạy ≤ 20 s)
- Soak (v1.3): `python3 tools/soak.py --seed 7 --days 10 --out soak.json` → đạt khi `crashes == 0`
- Bench (v1.3, cần Chrome/Chromium; đặt `CHONOI_BROWSER=<đường dẫn>` nếu không tự tìm thấy):
  `python3 tools/bench.py --seed 42 --duration 30 --out bench.json`
- Bằng chứng theo phase: `bash docs/proof/phase-1|2|3/run_proof.sh` (ghi đè file trong `docs/proof/`);
  Phase 4 là `docs/proof/phase-4/{bench,soak}.json` tạo bằng hai lệnh trên.
- Kiểm danh sách thành viên: `python3 tools/check_team.py`
- Bản chơi GUI (`client/`, sáng tạo của nhóm): chạy `python3 -m http.server 8099` ở **gốc repo**, mở
  `http://127.0.0.1:8099/client/`. Không chạy server trong `client/` (client đọc `../game.contract.json`),
  không dùng cổng 8000 (`chonoi.live` mặc định chiếm).
- Chơi thử luật Python trên trình duyệt: `python3 -m chonoi.live --mode gather|quan` (WASD, E, Space, R)
- Skill của nhóm: `python3 .agents/skills/pre-push-check/check.py` · `python3 .agents/skills/verify-tag/verify_tag.py`

## Cấu trúc & quy ước
- (Starter Python là TÙY CHỌN; nhóm có thể dùng ngôn ngữ khác nếu giữ Test Contract.) Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa; nếu phải sửa thì báo cả nhóm và ghi lại lý do.
- Luật chơi của nhóm: `chonoi/sim/{gather,quan,day,shop}.py`. Bench/soak: `tools/bench.py`, `tools/soak.py`, `client/bench.html`.
- Ticket từng phase: `docs/contracts/ticket-0N-*.md` (nguồn chuẩn). Đổi `contract_version` → cập nhật `CHANGELOG.md`,
  `docs/verification/phase-n.md` và ghi lý do ngay tại test nào phải sửa.
- **Số liệu chỉ đọc từ `game.contract.json` / dữ liệu**, không hard-code trong luật. Client cũng đọc contract; đổi kiểu
  một khóa (ví dụ `fish_initial` từ mảng sang số) phải sửa cả client.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.
- Phần sáng tạo chỉ ở `client/`; headless và JSONL giữ đúng Test Contract.

## Nên tránh
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo cả nhóm (đổi hợp đồng ảnh hưởng mọi module).
- Không làm hỏng nhánh chính: trước khi đẩy, chạy `pre-push-check` (mã 0 mới được push).
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO; ghi cả giờ hỏi và câu trả lời.
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi lý do đổi test trong commit.
- Không di chuyển hay gắn lại tag đã đẩy khi chưa hỏi Integrator.

## Quy tắc làm việc với agent
- Mỗi agent một việc rõ ràng (một lát). Cho agent đọc PRD/ticket đúng phase và hợp đồng kho trước.
- Chốt người sở hữu từng file (nhất là test và `client/src/*`) trước khi giao việc cho nhiều agent song song.
- **"Xong"** = `pre-push-check` đạt **và** (nếu đổi `client/`) chơi thử trên trình duyệt hết vòng lặn → quán → chợ
  **và** có bằng chứng (mô tả commit hoặc `docs/proof/`). Test headless xanh chưa đủ.
- Agent chỉ commit/push khi người phụ trách yêu cầu rõ. Commit từ máy ai thì tính cho tài khoản người đó, nên người đó
  phải đọc lại diff trước khi đẩy.
- Mỗi phiên agent ghi một dòng vào `docs/ai-usage-log.md` (việc, kết quả kiểm, AI sai ở đâu).
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem README, mục "Tự do sáng tạo").

## Skills / hooks của nhóm
- **`pre-push-check`** (`.agents/skills/pre-push-check/`): dùng trước mỗi lần `git push`, trước khi gắn tag, hoặc khi
  agent báo xong một lát. Một lệnh chạy contract, `check_team`, toàn bộ unittest, smoke headless gather/quan/day
  (1 Ngày ≤ 20 s), cú pháp JS `client/src`, file nhạy cảm; in dòng tóm tắt để dán vào commit. Mã 1 thì không push.
- **`verify-tag`** (`.agents/skills/verify-tag/`): dùng ngay sau khi gắn tag `phase-n`/`v*` và trước khi viết
  `docs/verification/phase-n.md`. Xuất mã của tag bằng `git archive` ra thư mục tạm, chạy unittest + headless ở đó,
  kiểm tag đã đẩy đúng commit, in bảng Markdown để dán vào bằng chứng.
