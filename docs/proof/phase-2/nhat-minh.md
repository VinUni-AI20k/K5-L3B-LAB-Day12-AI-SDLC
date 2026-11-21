# Nhật Minh — Phase 2: cá và vợt

Nhánh: `feat/nhat-minh`. Ticket: **02 fish** và **07 net**.
Nguồn: spec/ticket nhóm, prefactor `c84eac9`, snapshot có Cá Sấu `6187354`.
Không Git merge, checkout, commit, push hoặc thay ref `main` trong lượt triển khai này.

## Kết quả

- Cá: `fish.py` đọc toàn bộ tham số từ tuning, giữ 8 đàn đầu từ manifest; bơi/phản xạ theo từng loài;
  đổi hướng trước bơi; sinh sau bơi; chuẩn hóa trọng số theo loài còn điểm hợp lệ; tối đa 12 đàn theo preset.
- `random_fish:false` tắt mặc định/bơi/sinh, giữ fixture đứng yên và tăng tuổi. Đàn mới có tuổi 0,
  không bơi hoặc bị bắt cho tới bước sau. ID tăng qua cả đàn đã bị bắt, RNG qua `Streams`.
- Vợt: cấp 0 dùng lõi; cấp 1/2 đọc bán kính/số đàn từ dữ liệu, duyệt theo numeric ID, giữ đàn thiếu chỗ
  và thử đàn kế; chỉ đặt cooldown sau ít nhất một lần bắt thành công. Không bật extension thì cùng byte với lõi.
- Net dùng `active_upgrades`, không dùng nâng cấp vừa mua trong shop hiện tại. Owner `day` truyền cấp đang hiệu lực khi dựng gather.

## Kiểm chứng

```powershell
$env:PYTHONPATH = 'tests;.'
python3 -m unittest discover -s tests -v
python3 tools/check_nhat_minh.py
python3 tools/check_nhat_minh.py --with-integration-patches --out docs/proof/phase-2/with-proposed-hooks.txt
```

Command thứ hai/ba giải nén dependency vào thư mục tạm và phủ đúng source/test của Nhật Minh;
không đổi branch, contract hoặc file framework trong bản làm việc.
Ref mặc định là `6187354e76eb31adec90ecd8dfea1d305d6d6427`, phải có object này trong Git local;
có thể truyền `--prefactor-ref` tương đương khi cần. Command không fetch.

| Bộ kiểm | Bằng chứng | Phạm vi |
|---|---|---|
| Bản làm việc, contract v1.0 giữ nguyên | [local-all-tests.txt](local-all-tests.txt) | **104 test qua, 2 class skip**: cá v1.1 và day/net chưa có data/hook; component net/fresh/current vẫn chạy |
| Dependency v1.1 + source/test Nhật Minh | [all-assigned-v11.txt](all-assigned-v11.txt) | 168 test qua trước khi thêm class day/net CLI; các ca cá chạy headless thật |
| Dependency v1.1 + patch bàn giao trong thư mục tạm | [with-proposed-hooks.txt](with-proposed-hooks.txt) | **174/174 qua, không skip**; thêm CLI day/net và current để kiểm đường truyền metadata; không kiểm migration kho v1.2 |

25 ca cá trong `tests/test_fish_rules.py` kiểm speed/range/biên/góc, tick 120/360, trần, clearance đúng 1 m,
hết điểm, chuẩn hóa trọng số, tuổi 0, bắt/xóa đàn, ID không tái sử dụng và JSONL tất định.
`tests/test_net_day_rules.py` kiểm cấp 0/1/2, giỏ gần đầy, hồi chiêu, không mục tiêu và current qua CLI thật.
`tests/test_gather_extensions.py` kiểm thêm lớp sim và tương tác với độ tươi.

Ba ca P1 (hái, bắt, ngất) so với commit `2b95df8` có JSONL và file kho giống từng byte;
[kết quả](legacy-byte-compatibility.txt) cũng xác nhận file framework/contract và ref main không đổi.

## Bàn giao Integrator

- [Patch metadata/day](integrator-extension-hooks.patch): truyền manifest `extensions`/`freshness` vào tuning
  khi bootstrap headless/live, và truyền `active_upgrades` từ day vào gather.
- [Patch dữ liệu net](integrator-net-data.patch): hai cấp 250/500, radius 4/6, giới hạn 2/3.
- Các patch chỉ được áp dụng trong thư mục tạm để kiểm chứng. File `game.contract.json`,
  `headless.py`, `live.py`, `runner.py`, `scenario.py`, `inventory.py` trong nhánh cá nhân vẫn giữ nguyên.
- API thay thế nếu caller giữ cả manifest: `GatherSim.from_contract(contract, scenario, streams, ids,
  day=..., active_upgrades=...)`. Caller không gọi gameplay khi paused.
- Chưa xác nhận shop mua nâng cấp/đổi Ngày vì đó là ticket 05 của Cao Minh. Net hoàn tất phần luật;
  manifest/bootstrap/day cần owner review và ghép, nên ticket 07 chưa ghi là hoàn tất tích hợp sản phẩm.

## Lý do đổi fixture hồi quy

Hai helper test P1 (`test_gather_actions.py`, `test_gather_rules.py`) đặt `random_fish:false` mặc định
để fixture bắt cá P1 giữ nguyên vị trí khi chạy trên v1.1. Assertion về luật/event không bị nới lỏng.
Test cá động ở file P2 riêng. File QA `test_gather_rules.py` được lấy từ dependency `c84eac9`,
không nhận là toàn bộ test mới của Nhật Minh. `monsters.py` giữ nguyên source của `6187354`.

Chưa có review của người. Xem tiếp [bàn giao Phase 3](../phase-3/nhat-minh.md).
