# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Test trên Windows PowerShell:
  `$env:PYTHONPATH = "tests;."; python -m unittest discover -s tests -v`
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

### 1. check-contract
- Mục đích: Kiểm tra Test Contract và tính tất định (determinism) của headless.
- Khi dùng: Sau khi sửa logic mô phỏng, trước khi merge và gắn tag Phase.
- Hướng dẫn: `.agents/skills/check-contract/SKILL.md`.
- Lệnh: `python .agents/skills/check-contract/check_contract.py`.
- Kiểm chứng: Đã chạy PASS với gather và quan ở chế độ Contract command và Local Python.

### 2. prepare-proof
- Mục đích: Chạy kiểm thử và thu thập bằng chứng Phase 1.
- Khi dùng: Trước khi tích hợp code hoặc bàn giao cho QA.
- Hướng dẫn: `.agents/skills/prepare-proof/SKILL.md`.
- Lệnh: `python .agents/skills/prepare-proof/prepare_proof.py`.
- Kiểm chứng: Unit tests PASS, gather PASS, quan PASS, determinism PASS.
- Bằng chứng: `docs/proof/phase-1/harness/20261121-104445-689582/`.

### Quy tắc chung
- Không thay đổi Test Contract khi chưa thống nhất với nhóm.
- Không sửa test chỉ để tạo kết quả PASS.
- Không tạo bằng chứng giả.
- Không tự động commit hoặc push.
- Người phụ trách phải kiểm tra kết quả trước khi bàn giao.

## Phase 1 — Quy trình phối hợp AI

### 1. Trước khi AI viết code
- Đọc PRD-0, hợp đồng tích hợp và yêu cầu của task.
- Xác định file được phép sửa theo docs/plan/phase-1.md.
- Không tự ý thay đổi game.contract.json hoặc docs/contracts/.
- Nếu yêu cầu chưa rõ, báo PO và ghi nhận vào docs/clarify.md.

### 2. Khi AI viết code
- Chỉ giải quyết một nhiệm vụ rõ ràng mỗi lần.
- Giữ nguyên Test Contract và khả năng chạy headless.
- Không tự ý thay đổi logic thuộc phạm vi người khác.
- Không sửa test chỉ để làm kết quả PASS.
- Không hard-code kết quả mô phỏng.

### 3. Sau khi AI viết code
- Kiểm tra git diff để biết AI đã thay đổi những gì.
- Chạy các bài test phù hợp với nhiệm vụ.
- Nếu sửa logic mô phỏng, kiểm tra determinism.
- Ghi lại kết quả PASS/FAIL thực tế.
- Nếu test thất bại, phải ghi rõ lỗi chưa khắc phục.

### 4. Trước khi bàn giao
- Chỉ commit file thuộc phạm vi được giao.
- Không commit API key, token hoặc .env.
- Ghi cách sử dụng AI vào docs/ai-usage-log.md.
- Đảm bảo người phụ trách đã kiểm tra thay đổi của AI.
- Thông báo cho Integrator trước khi tích hợp vào main.

### 5. Trách nhiệm Harness/Ops
- Người phụ trách: VThanh-Huy.
- Duy trì AGENTS.md và các skill của nhóm.
- Hỗ trợ QA kiểm tra Test Contract và determinism.
- Thu thập tiến độ qua docs/standup.md.
- Không tự đánh dấu công việc của người khác là hoàn thành.
