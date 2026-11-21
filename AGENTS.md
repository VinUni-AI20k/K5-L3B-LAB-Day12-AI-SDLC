# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm NhomABC

> Cập nhật qua các phase (lịch sử git lưu dấu vết). Ngắn gọn, có lệnh chạy thật.

## Lệnh chạy & kiểm chứng
- Kiểm tra thành viên & contract: `python3 tools/check_team.py`
- Chạy toàn bộ unit & smoke test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Headless (buổi sáng): `python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out_gather.jsonl --inventory-out kho.json`
- Headless (buổi tối): `python3 -m chonoi.headless --mode quan --seed 1 --inventory kho.json --ticks 600 --out out_quan.jsonl`
- Chơi thử trên trình duyệt: `python3 -m chonoi.live --mode gather|quan [--seed 1] [--port 8000]` (WASD / mũi tên: di chuyển, E: tương tác, Space: bắt cá, R: chơi lại, M: bật/tắt âm thanh)

## Phân công module (Phase 1 — khớp `TEAM.md`)
| Module | Thành viên (`handle`) | File phạm vi chính |
|---|---|---|
| **M1** (Sinh tồn `gather`) | Vũ Quang Huy (`huyvu-03`) | `chonoi/sim/gather.py` (`dive`/`surface`, oxy, ngạt, Máu, ngất) |
| **M2** (Thu hoạch + Kho `gather`) | Nguyễn Minh Quang (`QuangNEU`) | `chonoi/sim/gather.py` (giỏ LIFO, hái mặt nước, bắt cá, cập bến, kho) |
| **M3** (Khách `quan`) | Phùng Văn Thanh Cao (`ththanh8888`) | `chonoi/sim/quan.py` (lịch khách, giữ chỗ nguyên liệu, kiên nhẫn, rời đi) |
| **M4** (Bếp + Kinh tế `quan`) | Nguyễn Nhật Minh (`NhMinh-2610`) | `chonoi/sim/quan.py` (interact bếp/bàn, nấu, bưng, phục vụ, tiền, tip, uy tín) |
| **M5** (UI + Âm thanh + AI Harness) | Vũ Quang Thanh (`thanhvu101`) | `chonoi/web/`, `chonoi/live.py`, `AGENTS.md`, `.agents/skills/`, `docs/ui-contract.md` |
| **M6** (Hợp đồng + QA + Tích hợp) | Nguyễn Như Duy An (`K0heii`) | `docs/contracts/`, `chonoi/scenario.py`, `tests/`, `docs/verification/` |

## Cấu trúc & quy ước
- Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa khung lõi; nếu bổ sung (như phục vụ asset tĩnh `/assets/` trên `live.py`) phải giữ tương thích 100% với Test Contract.
- Luật chơi của nhóm: `chonoi/sim/gather.py`, `chonoi/sim/quan.py`.
- **Số liệu chỉ đọc từ `game.contract.json` (`tuning`) / dữ liệu**, tuyệt đối không hard-code trong luật.
- Mọi số ngẫu nhiên trong mô phỏng đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống. Cùng seed + inputs → output JSONL và kho giống nhau từng byte.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.

## Nên tránh
- Không tự ý sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo Integrator/PO (`M6` — Nguyễn Như Duy An).
- Không làm hỏng nhánh chính: luôn chạy `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` xanh trước khi đẩy hoặc mở PR.
- Không bịa yêu cầu: chỗ mơ hồ ghi vào `docs/clarify.md` và hỏi PO.
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi rõ lý do đổi test trong commit.

## Quy tắc làm việc với agent
- Mỗi agent phụ trách một lát công việc rõ ràng theo `phase-1-task.md`. Đọc `PRD0.md`, `docs/contracts/README.md` và `docs/ui-contract.md` trước khi sửa code.
- Agent làm xong phải chạy test, ghi bằng chứng vào `docs/proof/phase-1/` và cập nhật dòng của mình trong `docs/ai-usage-log.md`.
- Sáng tạo thêm (đồ họa, spritesheet, âm nhạc, hiệu ứng UI trên `chonoi.live`) chỉ nằm ở tầng hiển thị `chonoi/web/` và **tắt hoàn toàn ở headless**.

## Skills / hooks của nhóm
1. **`verify-phase`** (`.agents/skills/verify-phase/SKILL.md`):
   - **Khi nào dùng**: Trước mỗi lần commit/push, trước khi mở PR, hoặc khi M6 kiểm tra tích hợp cuối phase.
   - **Tác dụng**: Chạy kiểm tra `tools/check_team.py`, toàn bộ `unittest`, và kiểm tra tính tất định (cùng seed chạy 2 lần cho ra JSONL + file kho giống hệt từng byte).
2. **`ui-contract-sync`** (`.agents/skills/ui-contract-sync/SKILL.md`):
   - **Khi nào dùng**: Khi sửa HUD `chonoi/web/index.html`, cập nhật `docs/ui-contract.md`, hoặc thêm tài nguyên đồ họa / âm thanh (`chonoi/web/assets/`).
   - **Tác dụng**: Đối chiếu các trường UI đọc từ `GET /state` và lệnh gửi qua `POST /input` với `docs/contracts/README.md`, đảm bảo UI chịu lỗi khi thiếu trường/asset và không ảnh hưởng tới `chonoi.headless`.
3. **`sdlc-spec`** (`.agents/skills/sdlc-spec/SKILL.md`):
   - **Khi nào dùng**: Đầu mỗi Module/Task (M1.1, M2.1...) để phân tích yêu cầu và xuất Dev Spec + Test Spec ra `docs/specs/`.
   - **Tác dụng**: Đọc `phase-1-task.md`, `game.contract.json`, code khung → sinh tài liệu đặc tả chi tiết + ma trận AC, tự cập nhật `docs/ai-usage-log.md`.
4. **`sdlc-code`** (`.agents/skills/sdlc-code/SKILL.md`):
   - **Khi nào dùng**: Khi bắt đầu viết code vào `chonoi/sim/gather.py` hoặc `chonoi/sim/quan.py`.
   - **Tác dụng**: Đảm bảo 5 quy tắc bất biến (không hardcode, Streams RNG, sort_by_id, không phá framework, tắt sáng tạo ở headless). Tự cập nhật `docs/ai-usage-log.md`.
5. **`sdlc-test-report`** (`.agents/skills/sdlc-test-report/SKILL.md`):
   - **Khi nào dùng**: Sau khi code xong, trước khi commit/tag phase.
   - **Tác dụng**: Chạy unit test, headless, xuất bằng chứng JSONL vào `docs/proof/phase-N/`, tự điền `docs/verification/phase-N.md` và `docs/ai-usage-log.md`.
   - **Lệnh 1-click**: `python .agents/skills/sdlc-test-report/scripts/verify_and_report.py --phase 1 --mode gather --seed 1 --ticks 600 --pattern "test_smoke_*.py" --log-ai --author "QuangNEU"`
