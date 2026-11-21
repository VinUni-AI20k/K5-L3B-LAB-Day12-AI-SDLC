# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật. Người giữ: @linkiewinkie (PO); ai cần thêm thì nhắn.

## Lệnh
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Headless: `python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out.jsonl` (đổi `gather` thành `quan` để thử quán).
- Chơi thử trên trình duyệt: `python3 -m chonoi.live --mode gather` (hoặc `--mode quan`; mở địa chỉ in ra. Phím WASD, E, Space, R).
- Trên PowerShell, dùng `$env:PYTHONPATH = 'tests;.'` rồi chạy lệnh unittest. Kiểm tra `python3 --version` trước vì `headless_cmd` gọi `python3` trong tiến trình con.

## Đọc trước khi sửa
- Yêu cầu phase: PRD trên lab board (PO tóm tắt trong [kế hoạch](docs/plan/phase-1.md), có danh sách AC-P1-xx).
- Quyết định cho chỗ PRD mơ hồ: [docs/clarify.md](docs/clarify.md). **Tên event, tên trường và `data` lấy nguyên văn PRD-0 mục D/E.**
- Hợp đồng tích hợp: [docs/contracts/](docs/contracts/README.md) (kho, sự kiện, schema khách).

## Cấu trúc & ai giữ file

| File | Nội dung | Người giữ |
|---|---|---|
| `chonoi/sim/gather.py` | Lát 1: oxy, ngạt, Máu, ngất, dive/surface, giỏ LIFO, helper `_add_to_hold` | @justapea25 |
| `chonoi/sim/gather_harvest.py` | Lát 2: `try_gather` (hái), `try_catch` (bắt cá), mọc lại, hồi chiêu, `hold_full` | @LETHESHIYING |
| `chonoi/sim/quan_customers.py`, `chonoi/scenario.py` | Lát 3: `spawn_customers`, `tick_customers` (khách đến, chọn món, giữ chỗ, kiên nhẫn, khách rời) | @viethoang126 |
| `chonoi/sim/quan.py`, `chonoi/sim/quan_service.py` | Lát 4: interact, bếp, bưng, phục vụ, tiền, boa, uy tín, `quan_end` | @minhthu27 |
| `tests/test_integration.py`, `tests/test_regression.py`, `docs/verification/`, `docs/proof/` | Test hộp đen theo AC, bằng chứng | @Kaylez-TXL |
| `game.contract.json`, `docs/contracts/` | Contract, số liệu | @justapea25 |
| `docs/clarify.md`, `docs/plan/`, `AGENTS.md`, `.agents/skills/`, `README.md`, `CREDITS.md` | PO, harness AI, docs | @linkiewinkie |
| `docs/standup.md`, `docs/retro.md`, `CHANGELOG.md` | Scrum/Release | @minhthu27 |

- Khung do giảng viên cấp: `chonoi/{headless,inputs,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. **Không sửa**; bắt buộc phải sửa thì báo cả nhóm, một người làm, ghi lý do.
- Mỗi người một file test riêng (`tests/test_<lát>.py`); không sửa `tests/test_smoke_p1.py`, `tests/helpers.py`. Cần dữ liệu thì tự dựng scenario trong test.
- **Số liệu chỉ đọc từ `game.contract.json` / dữ liệu**, không hard-code trong luật.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.

## Quy tắc nhóm (Git)
- Nhánh ngắn `<handle>/<việc>`; commit nhỏ, thường xuyên; làm cặp thì ghi `Co-authored-by:`.
- Trước khi push: `git fetch && git rebase origin/main`, rồi chạy skill `run-tests`.
- Mở PR vào `main` trước phút 50; Lead (@justapea25) review, gộp, gắn tag. Test đỏ thì không gộp.
- Thứ tự gộp: helper giỏ (lát 1) trước lát 2; schema khách (lát 3) trước lát 4.
- Conflict ở file người khác giữ → giữ bản trên `main`, nhắn chủ file. Vướng quá 10 phút → báo nhóm, người dự phòng vào.
- File dùng chung (`TEAM.md`, `docs/ai-usage-log.md`): mỗi người chỉ sửa dòng/mục của mình, `git pull --rebase` ngay trước khi sửa.

## Nên tránh
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo cả nhóm (đổi hợp đồng ảnh hưởng mọi module).
- Không sửa file của người khác (bảng trên); cần đổi thì nhắn chủ file.
- Không làm hỏng nhánh chính: trước khi đẩy, chạy test.
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO.
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi lý do đổi test trong commit.

## Quy tắc làm việc với agent
- Mỗi agent một việc rõ ràng (một lát). Cho agent đọc PRD/ticket đúng phase, `docs/clarify.md` và hợp đồng trước.
- Agent chỉ sửa file của người đang dùng nó (bảng trên).
- Agent làm xong phải chạy test và ghi kết quả vào mô tả commit/PR; người đọc lại thay đổi trước khi đẩy.
- Ghi mỗi lần dùng AI vào mục của mình trong `docs/ai-usage-log.md` (công cụ, việc, AI sai ở đâu).
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem README, mục "Tự do sáng tạo").

## Skills / hooks của nhóm

| Skill | Khi nào dùng |
|---|---|
| [`run-tests`](.agents/skills/run-tests/SKILL.md) | Trước khi push/mở PR, sau khi gộp, trước khi gắn tag: unittest + smoke hai tiến trình + kiểm tra cùng seed giống từng byte |
| [`verify-phase`](.agents/skills/verify-phase/SKILL.md) | Phút 45–55 mỗi phase: điền `docs/verification/phase-n.md` theo AC-P{n}-xx với bằng chứng thật |
