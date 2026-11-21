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

- Mục đích: Chạy kiểm thử và thu thập bằng chứng cho Phase 1 và Phase 2.
- Khi dùng: Trước khi tích hợp code, bàn giao QA hoặc chuẩn bị release.
- Hướng dẫn: `.agents/skills/prepare-proof/SKILL.md`.

Lệnh Phase 1:

`python .agents/skills/prepare-proof/prepare_proof.py`

Lệnh Phase 2:

`python .agents/skills/prepare-proof/prepare_proof.py --phase2`

Trên Windows, khi lệnh python3 không hoạt động:

`python .agents/skills/prepare-proof/prepare_proof.py --phase2 --local-python`

- Bằng chứng Phase 1: `docs/proof/phase-1/harness/`
- Bằng chứng Phase 2: `docs/proof/phase-2/harness/`
- Chỉ ghi PASS khi các kiểm thử thực tế đều thành công.
- `--local-python` không xác nhận launcher gốc trong Test Contract hoạt động.
- QA chịu trách nhiệm xác nhận Acceptance Criteria.
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


## Phase 2 — Quy trình phối hợp AI và Harness

### 1. Nguồn yêu cầu và Test Contract

- Đọc `docs/prd-phase-2.md` và `docs/plan/phase-2.md`.
- Đọc `game.contract.json` trước khi sửa code.
- Phase 2 sử dụng Test Contract v1.1.
- Không tự ý thay đổi `game.contract.json` hoặc `docs/contracts/`.
- Khi phát hiện yêu cầu mơ hồ, trao đổi với PO hoặc Integrator.
- Không dùng suy đoán của AI thay cho PRD hoặc Contract.

### 2. Phân chia trách nhiệm

- Dev Lead: Phụ trách logic gather.
- Integrator: Phối hợp tích hợp giữa các module và giữ Contract.
- PO: Làm rõ yêu cầu và quy tắc sản phẩm.
- Demo Lead: Phụ trách giao diện và trình diễn.
- QA Lead: Kiểm thử và đánh giá Acceptance Criteria.
- Scrum/Release (VThanh-Huy): Duy trì AGENTS.md, hai skill và hỗ trợ thu thập bằng chứng.

Mỗi thành viên chỉ sửa các file thuộc nhiệm vụ của mình,
trừ khi có sự thống nhất của nhóm.

### 3. Kiểm tra Test Contract v1.1

Chạy:

`python .agents/skills/check-contract/check_contract.py --phase2`

Trên Windows nếu thiếu lệnh python3:

`python .agents/skills/check-contract/check_contract.py --phase2 --local-python`

Skill phải kiểm tra:

- Contract version 1.1.
- Headless gather.
- Headless quan.
- Headless day.
- Determinism với cùng seed và đầu vào.
- Day hoàn thành đúng trạng thái.
- Thời gian chạy một ngày mô phỏng không quá 20 giây.

Không được tự sửa Contract hoặc test để tạo kết quả PASS.

### 4. Chuẩn bị bằng chứng

Chạy:

`python .agents/skills/prepare-proof/prepare_proof.py --phase2`

Trên Windows:

`python .agents/skills/prepare-proof/prepare_proof.py --phase2 --local-python`

Bằng chứng được lưu tại:

`docs/proof/phase-2/harness/<timestamp>/`

Bộ bằng chứng gồm:

- Kết quả unit tests.
- JSONL cho gather, quan và day.
- Log thực thi và exit code.
- SHA-256 để đối chiếu determinism.
- Thời gian chạy day.
- Report tổng hợp PASS/FAIL.

Chỉ dùng bằng chứng thực tế. Không ghi PASS khi unit tests
hoặc kiểm tra bắt buộc còn thất bại.

### 5. Quy tắc sử dụng AI

- Giao cho AI một nhiệm vụ rõ ràng mỗi lần.
- Yêu cầu AI đọc tài liệu liên quan trước khi sửa code.
- Kiểm tra diff sau khi AI chỉnh sửa.
- Không để AI tự sửa Contract hoặc test để hợp thức hóa kết quả.
- Không cho AI tự động commit, push hoặc merge.
- Ghi cách sử dụng AI vào `docs/ai-usage-log.md`.
- Mọi kết quả do AI tạo ra cần được con người kiểm chứng.

### 6. Trước khi tạo Pull Request

- Chạy kiểm thử phù hợp với phần đã sửa.
- Kiểm tra `git diff --check`.
- Kiểm tra `git status` và danh sách file được stage.
- Không commit API key, `.env` hoặc dữ liệu nhạy cảm.
- Không commit các proof thất bại như bằng chứng hoàn thành.
- Không dùng Harness PASS để khẳng định mọi AC đã đạt.
- Thông báo QA và Integrator trước khi tích hợp vào main.
```

## 4. Kiểm tra sau khi lưu

Nhấn `Ctrl + S`, sau đó chạy:

```powershell
git diff --check
git diff --stat
git status --short
```

Chúng ta kỳ vọng `AGENTS.md` xuất hiện trong danh sách file đã chỉnh sửa, cùng với hai skill đã làm trước đó.

<box gap={2}>
  **Tiến độ vai trò Người 6**

  | Hạng mục | Trạng thái |
  |---|---|
  | Skill 1 — Check Contract | <icon name="check-circle" color="success" inline/> PASS với Local Python |
  | Skill 2 — Prepare Proof | Đã nâng cấp, còn chờ xác nhận unit tests PASS |
  | Tài liệu hai skill | Đã hướng dẫn cập nhật |
  | `AGENTS.md` Phase 2 | Đang thực hiện |
  | `docs/ai-usage-log.md` | Tiếp theo |
  | `docs/standup.md` | Tiếp theo |
  | Commit / PR | Chưa thực hiện |
</box>

**Lưu ý:** Unit Tests của Skill 2 trước đó vẫn có 31 FAIL do lệnh `python3`. Nếu bạn chưa khắc phục xong, chúng ta sẽ không ghi nhận `Overall: PASS` hoặc đưa bộ proof đó lên GitHub.

Sau khi lưu `AGENTS.md`, bước tiếp theo là cập nhật **`docs/ai-usage-log.md` và `docs/standup.md`**. Mình sẽ hướng dẫn cách chỉ thêm dòng của bạn, giữ nguyên các dòng của những thành viên khác để tránh xảy ra conflict một lần nữa.