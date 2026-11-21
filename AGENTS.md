# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Headless: `python3 -m chonoi.headless --mode gather|quan --seed 1 --ticks 600 --out out.jsonl`
- Chơi thử trên trình duyệt: `python3 -m chonoi.live --mode gather|quan` (mở địa chỉ in ra; WASD, E, Space, R)
- Smoke hai tiến trình + bằng chứng: `python3 tools/smoke_proof.py --phase phase-1` (ghi `docs/proof/phase-1/`)
- Kiểm HUD + bằng chứng (cần Node.js): `python3 tools/hud_check.py --phase phase-1` (ghi `docs/proof/phase-1/hud.md`)
- Windows (Git Bash): `PYTHONPATH="tests;."` (dấu `;`), cần lệnh `python3` cho test hộp đen; không sửa `headless_cmd` trong contract.

## Đề bài (đọc trước khi code)
- Phase 1: [`docs/prd/phase-1.md`](docs/prd/phase-1.md) — PRD-0 + Test Contract v1.0 (luật từng bước ở mục F, sự kiện ở mục E, scenario ở mục D).
- Kế hoạch / chia lát: [`docs/plan/phase-1.md`](docs/plan/phase-1.md), người làm ở [`TEAM.md`](TEAM.md).
- **Phase 4 (đang làm):** [`docs/prd/phase-4.md`](docs/prd/phase-4.md) — TICKET-04 phát hành v1.0.0 (bench, soak, cảnh báo + tương phản cao, đóng gói, Release). Kế hoạch: [`docs/plan/phase-4.md`](docs/plan/phase-4.md). Nhánh ngắn → PR vào `main`.
- **Phase 3:** [`docs/prd/phase-3.md`](docs/prd/phase-3.md) — TICKET-03 kho cá thể + độ tươi (Contract v1.2). Quyết định + bảng tác động + thứ tự tích hợp: [`docs/adr/0001-kho-ca-the-do-tuoi.md`](docs/adr/0001-kho-ca-the-do-tuoi.md). Làm trên nhánh `v1.2`, KHÔNG push v1.2 thẳng `main`.
- **Phase 2:** [`docs/prd/phase-2.md`](docs/prd/phase-2.md) — TICKET-02 + Test Contract v1.1 (số chuẩn mục 1, vòng ngày/Shop mục 2, thứ tự xử lý mục 4.5). Kế hoạch: [`docs/plan/phase-2.md`](docs/plan/phase-2.md).

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
| Skill | File | Khi nào dùng |
|---|---|---|
| `run-tests` | [`.agents/skills/run-tests/SKILL.md`](.agents/skills/run-tests/SKILL.md) | Sau mỗi thay đổi ở `chonoi/` hoặc `tests/`, trước khi push lên `main` và trước khi gắn tag. Chạy cả bộ bằng 1 lệnh, báo từng test hỏng, không sửa test cho xanh. |
| `smoke-proof` | [`.agents/skills/smoke-proof/SKILL.md`](.agents/skills/smoke-proof/SKILL.md) + [`tools/smoke_proof.py`](tools/smoke_proof.py) | Phút 25 (thử xuất kho thật), phút 45–55 (trước tag), khi đổi hợp đồng kho. Chạy smoke gather → quan của PRD mục G, lưu bằng chứng vào `docs/proof/<phase>/`. |
| `hud_check` (tool) | [`tools/hud_check.py`](tools/hud_check.py) + [`tools/hud_harness.js`](tools/hud_harness.js) | Sau khi sửa `chonoi/web/` hoặc đổi trường snapshot, và trước tag. Dựng 5 trạng thái thật bằng headless, vẽ HUD ở 4 bề rộng bằng canvas giả: kiểm lỗi vẽ, chữ đè/tràn, đủ trường HUD tối thiểu DoD, kho khả dụng; ghi `docs/proof/<phase>/hud.md`. Cần Node.js. |

Cách viết test cho một lát (mẫu: `tests/test_gather_lat1.py`): đọc mục F của PRD → viết test hộp đen qua headless trước, thấy fail đúng lý do → viết luật → chạy `run-tests`.
