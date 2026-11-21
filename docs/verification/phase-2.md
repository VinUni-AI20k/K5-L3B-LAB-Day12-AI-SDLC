# Kiểm chứng phần tích hợp Phase 2

Nguồn: `docs/tickets/TICKET-02.md` do PO/người dùng cung cấp. Nhánh triển khai từ `origin/dev` dc9952b (đã có PR #11, #13). Đây là kiểm chứng phần việc trong PR, chưa phải chứng nhận bàn giao/tag trên main.

## Hành vi và bằng chứng
- TICKET-02 mục 2, 4.1, 4.4–4.5: `day --days 1..5`, kế hoạch D1–D5, kho gather→quan trong bộ nhớ, tiền/earned/uy tín xuyên Ngày. `tests/test_day_p2.py`: chạy đủ 5 Ngày, kết thúc sau Shop, event giữ pha/Ngày cũ và snapshot đổi pha về tick 0. `smoke-local/day.jsonl`, `day-repeat.jsonl` giống từng byte.
- Shop: oxygen 200/400 → 45/60 s; hp 250/500 → 4/5 Máu. Test mua đúng giá, không đủ tiền/tối đa/không hỗ trợ, buy trước done ở bước cuối, tự đóng sau 600 bước. `smoke-local/upgrade-day.jsonl` kiểm Ngày 2 có oxy 2700, hp 4, money 0, earned 450 và score 750.
- Pause mục 4.2: tick ngoài tăng; sim_tick/phase_tick/cá/quái/oxy/Shop đứng yên. Resume chạy gameplay cùng bước; buy trong pause bỏ qua và không chạy lại; nút giữ xuyên pha không sinh cạnh mới. Có test cho gather/Shop và kiểm UI thực.
- Cá sấu: patrol/chase/detect/exit/depth/hit/recoil/giỏ rơi/bất tử đọc dữ liệu. Test tuning patrol_speed=0, chase_speed=0, hit radius, loss ratio, invuln và recoil khác preset; bước cuối recoil không hit, bước kế mới được xét. Không chỉnh chuẩn dữ liệu cá sấu.
- Live: menu Chơi/Thoát; intro ngày (tự chuyển 4s/phím), intro quán nhập kho/món khả dụng, kết quả ngày, Shop và Summary. Pause overlay có Tiếp tục/Về menu. Màn trình bày đứng ngoài tick gameplay của headless.
- HUD: giỏ theo loại/đã lấy-cần, Máu/oxy/thời gian/độ sâu/hồi bắt; gợi ý E và cảnh báo quái/oxy. Quán đọc 6 tên món, bếp/tiến độ, kiên nhẫn đổi màu dưới 25%, tay và kho trừ reserved. Chữ canvas tối thiểu 18px. Quái vẽ theo vị trí snapshot, không tự chạy mô phỏng JS.
- `tools/smoke_p2.sh` còn kiểm gather→file kho→quan độc lập và đo 1 Ngày <20s trên máy hiện tại. Thời gian cụ thể ở `smoke-local/summary.json`; đây không thay cho đo trên máy chấm.

## Kiểm UI thực
Ở 1280×720 đã kiểm menu, kế hoạch, HUD sáng có M1, pause, nhập kho, kết quả, Shop mua oxygen+hp với ví đúng 450, pause/resume Shop và đóng Shop tới Summary 1 Ngày. Cấp mua 1 hiển thị ngay, active vẫn 0 trong Shop. `ui/gather.jpg`, `ui/pause.jpg`, `ui/shop.jpg`, `ui/summary.jpg`.
Fixture UI rút thời lượng gather/quan còn 1 tick và khai tiền đầu kỳ 450 để kiểm điều hướng/mua; không dùng fixture này làm bằng chứng đã chơi phục vụ đầy ca. Chưa có phép đo FPS trung bình trên máy chấm.

## Thay đổi khung/hợp đồng cần cả nhóm đọc
- `headless.py`: bật day/days và inputs v1.1.
- `runner.py`: tick ngoài/sim_tick, pause, bọc event có day và snapshot khi đổi pha; chung cho CLI/live.
- `inputs.py`: buttons v1.1, buy chỉ chạy đúng frame, live giữ cạnh và buy một lần.
- `scenario.py`: nhận day/gather/quan, kiểm tiền/cấp/override kế hoạch và cấm quan.stock/reputation trong day; kiểm miền sâu quái theo tuning.
- `contract.py`, `game.contract.json`: thêm và kiểm dữ liệu Shop theo mục 4.1; lệnh chạy mặc định live day. Schema file kho không đổi.
- `live.py`, web: trình bày vòng ngày/pause/UI; vẫn dùng Session, không nhân đôi luật.

## Lý do đổi test P1
`test_smoke_p1.py` bỏ giả định day bị từ chối: day nay là mode lõi v1.1. Bỏ giả định attack đúng kiểu phải báo mã 2: mục 4.2 yêu cầu bỏ qua khi mở rộng chưa bật. Giữ kiểm mode `river`, nút lạ `jump` và toàn bộ test luật cũ khác. Unit loader mặc định v1.0 vẫn giữ hành vi cũ; CLI v1.1 truyền buttons rõ ràng.

## Kết quả lần kiểm cuối
163 test: OK. Smoke tích hợp kho, tất định 1 Ngày, nâng cấp 2 Ngày: OK. Chi tiết thời gian và SHA-256 ở `smoke-local/summary.json`.

## Lệnh lặp lại
```bash
tools/smoke_p2.sh
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 -m chonoi.live --mode day
```
Bằng chứng test nằm ở `docs/proof/phase-2/smoke-local/tests.log`. Cần người trong nhóm review trước khi đưa lên main/tag; chưa tự tag hoặc merge main.
