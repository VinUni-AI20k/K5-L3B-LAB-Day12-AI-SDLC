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
- **File khung đã sửa cho v1.1 (TV6, lát 4 — T240–T245, T248)**, lý do: Test Contract v1.1 bắt buộc `--mode day`, nút mới và pause, khung cũ chặn trước khi tới sim:
  - `headless.py`: `--mode day`, `--days` 1–5 (mã 2 khi sai / dùng với mode khác / kèm `--inventory*`); contract thiếu `tuning.day_plan`/`tuning.shop` → mã 2 "chờ TV1"; biến môi trường `CHONOI_CONTRACT` chỉ để test trỏ contract fixture (`tests/fixtures/contract-v1.1-day.json`).
  - `inputs.py`: nút `pause`, `shop_done`, `attack`, `photo` + chuỗi `buy` (chỉ tại frame khai báo); bộ nút chọn theo `contract_version` (v1.0 vẫn từ chối `attack` như P1 → test cũ không vỡ trước khi TV1 nâng contract).
  - `runner.py`: tách `tick`/`sim_tick`/`phase_tick`; pause là lớp bọc chung ở `Session.step` cho cả 3 mode (`paused`/`resumed`, `state:"paused"`); vỏ event `day`, snapshot đổi pha, `end.days_completed`; sự kiện tick 0 của day ghi trước snapshot tick 0.
  - `scenario.py`: khối `day {money,earned,reputation,upgrades,day_plan}`, `gather.monsters[]`, `fish[].age_ticks`; cấm `quan.stock`/`quan.reputation` khi chạy day.
  - `live.py`: `--mode day`, `set_input` nhận `pause`/`shop_done`/`buy`, `meta` theo pha + `menu`, `day_plan`, `shop`, `upgrades`; snapshot thêm `paused`.
  - Mới: `chonoi/sim/day.py` (DaySim), `chonoi/sim/shop.py` (ShopSim). Gọi GatherSim/QuanSim qua giao diện hiện có; ngữ cảnh Ngày tạm truyền bằng bản sao tuning (cấp oxy/Máu, lọc menu theo kế hoạch, spawns theo `from_day`) tới khi có T246/T230.

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
- **pre-push-check** (`.agents/skills/pre-push-check/`): dùng trước mọi lần push, trước khi tag phase-N, và sau khi agent sửa code. Chạy unit test + tất định headless (gather/quan, cùng seed so byte) + exit 2 khi đầu vào sai. Lệnh: `.agents/skills/pre-push-check/check.sh [--save docs/proof/phase-<n>]` (env `SEED`, mặc định 1).
- (skill thứ 2: TODO)
