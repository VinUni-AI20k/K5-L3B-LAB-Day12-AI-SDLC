# AGENTS.md — Hướng dẫn chung cho mọi AI Agent của nhóm

> **Cảm hứng thiết kế:** Game mô phỏng 2D theo phong cách **Dave the Diver** phiên bản Miền Tây Sông Nước:
> - **Ban ngày (`gather`):** Út Sen lặn lòng sông Mekong bắt cá, hái hoa, quản lý bình dưỡng khí Oxy, né ngạt nước và mang đồ về ghe cập bến xuất kho nguyên liệu.
> - **Ban đêm (`quan`):** Quán Ăn Chợ Nổi lên đèn (tương tự nhà hàng Bancho Sushi), tiếp đón khách ghe, kiểm tra kho, nấu nướng lẩu/cá nướng, bưng bê phục vụ trước khi khách hết kiên nhẫn, thu tiền, nhận tip và tích lũy uy tín nhà hàng.

## Hướng dẫn điều hướng nhanh cho Agent
Khi được phân công một nhiệm vụ, Agent hãy đọc ngay:
1. Bản đồ phân công & tiến độ 5 Dev: [`docs/plan/tasks-summary.md`](docs/plan/tasks-summary.md)
2. File đặc tả nhiệm vụ gameplay chi tiết:
   - DEV 1: [`docs/plan/task-1-gather-survival.md`](docs/plan/task-1-gather-survival.md) (Lặn, Oxy, Ngạt nước, Máu, Cập bến ghe)
   - DEV 2: [`docs/plan/task-2-gather-harvest.md`](docs/plan/task-2-gather-harvest.md) (Hái Bông Điên Điển, Bông Súng, Bắt Cá Linh, Cá Lóc, Giỏ LIFO)
   - DEV 3: [`docs/plan/task-3-quan-customers.md`](docs/plan/task-3-quan-customers.md) (Khách ghe đến, Xếp bàn ăn, Thanh kiên nhẫn, Bỏ về)
   - DEV 4: [`docs/plan/task-4-quan-inventory-menu.md`](docs/plan/task-4-quan-inventory-menu.md) (Kho khả dụng, Kiểm tra menu, Khóa giữ chỗ nguyên liệu)
   - DEV 5: [`docs/plan/task-5-quan-kitchen-serving.md`](docs/plan/task-5-quan-kitchen-serving.md) (Bếp nấu, Chín món, Bưng bê, Phục vụ, Tiền, Tip, Uy tín)
   - VIỆC CHUNG (FE & Visuals): [`docs/plan/shared-fe-visuals.md`](docs/plan/shared-fe-visuals.md) (Đồ họa Web, Nước sông Tiền, Quán nổi đèn lồng đêm, Camera LERP, Âm thanh)

## Lệnh thực thi & Kiểm tra
- Chạy smoke test:
  * Windows: `py -3 -m unittest discover -s tests -v`
  * Linux / Mac: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Kiểm tra danh sách thành viên: `py -3 tools/check_team.py`
- Chạy headless (CLI): `py -3 -m chonoi.headless --mode gather|quan --seed 1 --ticks 600 --out out.jsonl`
- Chơi thử trên trình duyệt: `py -3 -m chonoi.live --mode gather|quan` (WASD, E, Space, R)

## Cấu trúc & Quy ước bắt buộc
- Khung starter do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa khung nếu không cần thiết.
- Logic luật chơi của nhóm: `chonoi/sim/gather.py` và `chonoi/sim/quan.py` (tìm các khối `TODO(nhóm)`).
- **Số liệu chỉ đọc từ `game.contract.json` / `tuning`**, tuyệt đối không hard-code số liệu trong logic luật.
- Mọi số ngẫu nhiên bắt buộc đi qua `Streams` (`chonoi/rng.py`); **không dùng random toàn cục, không dùng đồng hồ hệ thống (`time.time()`)**.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp ID mới bằng `IdAllocator`.
- **Tầng hiển thị web (`chonoi/web/index.html`) là View thụ động:** chỉ đọc snapshot từ `/state` và gửi phím `/input`, không can thiệp vào logic sim hay phá vỡ chế độ headless.

## Nên tránh
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa thống nhất cả nhóm.
- Không làm hỏng nhánh chính: trước khi tạo commit hoặc push, luôn chạy bộ test đảm bảo 100% test cases đều pass (xanh).
- Không sửa test cho xanh khi luật sai; phải sửa luật chuẩn theo contract.

## Skills của nhóm
- `gather-sim` (`.agents/skills/gather-sim/`): Chuyên gia mô phỏng lặn, oxy, ngạt, hái bông, bắt cá và giỏ đồ LIFO trong `chonoi/sim/gather.py`.
- `quan-sim` (`.agents/skills/quan-sim/`): Chuyên gia mô phỏng quán ăn, vòng đời khách, giữ chỗ kho, bếp nấu và thanh toán trong `chonoi/sim/quan.py`.
- `chonoi-qa` (`.agents/skills/chonoi-qa/`): Chuyên gia kiểm thử tự động, xác thực tính tất định byte-for-byte và test contract.
- `mekong-ui` (`.agents/skills/mekong-ui/`): Chuyên gia đồ họa Canvas/WebGL sông nước miền Tây cho `chonoi/web/index.html`.
