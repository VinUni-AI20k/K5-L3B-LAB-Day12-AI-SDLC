# Phase 1 — Bằng chứng lát 4 của chur04

Ngày kiểm chứng: 21/11/2026. Nguồn yêu cầu: PRD-0 Phase 1 D/E/F do người dùng cung cấp, đối chiếu với `docs/plan/phase-1.md` và hợp đồng tích hợp hiện có. Đây là bằng chứng phần việc của Vũ Văn Chủ, chưa phải xác nhận DoD toàn nhóm hay tag `phase-1`.

## Phạm vi đã làm

- `chonoi/sim/quan_service.py`: chọn một mục tiêu theo khoảng cách/loại/id, lấy đơn reserved cũ nhất, tiêu phần giữ, nấu, bưng payload gắn order_id, phục vụ, chốt boa, thu tiền, cập nhật uy tín, dọn đơn và đóng ca.
- `chonoi/sim/quan.py`: nối các bước theo PRD F, thêm phase_tick phục vụ tích hợp lịch khách; không sinh khách tự động trong thay đổi này.
- Hỗ trợ tích hợp cần thiết: chuẩn hóa khách fixture, giữ chỗ, kiểm liên kết payload/timer; giảm kiên nhẫn và hủy món khi khách rời. Các hàm dùng chung đã ghi ở [clarify](../../clarify.md) để lát 3 không giảm timer/thu tiền/hủy đơn hai lần.
- Không đổi contract JSON, file kho, bộ test có sẵn, runner, scenario loader hoặc UI.

## Chạy lại

Từ gốc repo, kiểm riêng lát 4 (Windows dùng `python`, Linux/macOS có thể dùng `python3`):

```powershell
python -m unittest discover -s tests -p test_quan_service.py -v
```

Chạy bằng input thật qua CLI:

```powershell
python -m chonoi.headless --mode quan --seed 7 --ticks 1200 --scenario docs/proof/phase-1/chur04-service-scenario.json --inputs docs/proof/phase-1/chur04-service-inputs.json --snapshot-every 360 --out service.jsonl
```

Chơi thử bằng WASD/E với khách dựng sẵn:

```powershell
python -m chonoi.live --mode quan --scenario docs/proof/phase-1/chur04-service-scenario.json
```

Fixture rút ca còn 1171 tick (~19.5 giây); bắt đầu tại bếp, E để nấu, chờ 6 giây, nhả/bấm E để bưng rồi đi tới bàn T1 để phục vụ. Bằng chứng tự động dùng chuyển động thật, không dịch chuyển vị trí trong CLI.

## Kết quả thực tế

- **28/28 test mới đạt**, gồm luồng hoàn chỉnh và các biên: bán kính, ưu tiên mục tiêu/id, đơn cũ nhất, cạnh lên, không bưng hai món, nhận đúng order_id, sắp nguyên liệu, tuổi món ready, deadline kiên nhẫn, boa floor, chốt boa, kẹp uy tín, thu tiền đúng một lần, đóng ca, hủy món không hoàn hàng, fixture lỗi thoát 2 trước ghi output, không làm biến đổi scenario khi restart.
- **60/60 test toàn repo đạt** khi dùng launcher Python hiện có; log đầy đủ: [chur04-tests.txt](chur04-tests.txt).
- Môi trường Windows này có `python` 3.15.0 nhưng `python3` trỏ tới Microsoft Store. Lệnh test chuẩn ban đầu thất bại 20 test hộp đen với mã 9009 vì chưa chạy được Python. Khi kiểm toàn bộ suite, chỉ thay launcher của `helpers.headless_cmd` sang `sys.executable` trong tiến trình test, không thay assertion, file contract hay nguồn test. Cách này cũng đã được ghi trong bằng chứng mở rộng có sẵn của repo.
- `python tools/check_team.py`: OK, 6 thành viên, có `chur04`.
- Hai output headless giống nhau từng byte. SHA-256: `1f97f7ec70b9653503c92d872281f707585331a73ddf8f44251a2d0892acf666`.
- Output thật: [chur04-service-output.txt](chur04-service-output.txt), nội dung JSONL UTF-8, dùng đuôi `.txt` để lưu được bằng chứng theo `.gitignore` hiện tại.

| Tick event | Event | Quan sát |
|---|---|---|
| 1 | cook_started | B1, C1, cá lóc nướng trui, tiêu ca_loc ×1, base_price=60 |
| 361 | dish_ready, dish_picked | Đủ 360 tick nấu, bưng ngay tick chín |
| 571 | served | Đúng đơn C1, kiên nhẫn còn 3029, tip=12 |
| 1171 | paid | Ăn đủ 600 tick, amount=72, reason=finished_eating |
| 1171 | quan_end | money=earned=shift_earned=72, reputation=3.2 |
| 1171 | end | reason=time, score=372 |

Chạy lại toàn bộ suite trên Windows với launcher thay tạm trong tiến trình:

```powershell
@'
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, 'tests')
import helpers
cmd = helpers.headless_cmd()
if cmd == ['python3', '-m', 'chonoi.headless']:
    cmd[0] = sys.executable
with patch.object(helpers, 'headless_cmd', return_value=cmd):
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover('tests'))
sys.exit(0 if result.wasSuccessful() else 1)
'@ | python -
```

## Phần còn lại khi bàn giao

- Nhung (lát 3): nối lịch khách cuối bước, RNG chọn món, `no_dish`, kiểm schema scenario đầy đủ (trường lạ, miền dữ liệu, liên kết bếp/bàn). Tái sử dụng hoặc chuyển các hàm timer/chuẩn hóa/dọn đơn hiện có, không gọi hai lần.
- Khải: các TODO gather còn nguyên; smoke test đạt không đồng nghĩa luật oxy/hái/bắt đã xong.
- QA/Integrator: chạy lại trên main sau tích hợp, review chéo và gắn tag đúng quy trình nhóm. Bằng chứng này thuộc working tree trên nhánh `feat/quan-service-phase-1-chur04`, chưa có commit/push/tag mới.
- Chưa thực hiện chơi thử trực tiếp bằng người; đã kiểm mô phỏng và headless tự động. Không ghi nhận trao đổi giảng viên, review của đồng đội hoặc commit cá nhân chưa xảy ra.
