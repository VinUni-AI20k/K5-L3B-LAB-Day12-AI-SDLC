# Ma trận truy vết Phase 1

Cập nhật 2026-11-21 trên `main` sau PR #17. Nguồn yêu cầu: PRD-0 (lab board, tab Phase 1) mục 2, A đến G. Mã AC do nhóm đặt (`AC-P1-xx`).
Chạy lại toàn bộ: `PYTHONPATH=tests:. python -m unittest discover -s tests` (157 test) và `python tools/smoke_phase1.py` (27 mục), xem [docs/proof/phase-1/smoke.md](../proof/phase-1/smoke.md).
Cột kết quả ghi trung thực: **đạt**, **đạt một phần** hoặc **chưa đạt**.

## A. Buổi sáng: Lặn và Hái (`gather`)

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P1-01 Bơi: tốc độ `swim_speed`, tăng/giảm tốc tối đa `ramp_max_ticks`, chặn mép, `d` không âm, hướng mặt | Test hộp đen đo quãng đường và vận tốc qua headless | `tests/test_smoke_p1.py` (nhóm `move_*`, ramp, chặn mép) | Đạt |
| AC-P1-02 Oxy: trừ 1 mỗi tick dưới nước, hồi 6 mỗi tick ở mặt nước, kẹp trần; `dive`, `surface`, `oxygen_empty` | Test từng luật qua `Session`; đối chiếu PRD-0 mục F | `tests/test_gather_rules.py` (lớp `Oxygen`), [gather.md](../proof/phase-1/gather.md) | Đạt |
| AC-P1-03 Ngạt, Máu, ngất: nhịp `choke`, reset khi nổi, `faint` rơi giỏ theo LIFO, `gather_end` `fainted` với kho rỗng | Test luật và test payload | `tests/test_gather_rules.py` (`Choking`), `tests/test_gather_prd.py` | Đạt |
| AC-P1-04 Hái nút: chỉ ở mặt nước, trong bán kính, hòa theo id, `hold_full`, nút mọc lại sau `regrow_s`, giữ phím chỉ hái một lần | Test luật | `tests/test_gather_rules.py` (`Harvest`) | Đạt |
| AC-P1-05 Bắt cá: chỉ dưới nước, trong tầm, đúng sản lượng từng loài, hồi chiêu `catch_cooldown_s`, `hold_full` không hồi chiêu | Test luật | `tests/test_gather_rules.py` (`Catching`) | Đạt |
| AC-P1-06 Cập bến thắng hái cùng lần bấm; hết giờ `time`; ngất ưu tiên cao nhất | Test luật và smoke | `tests/test_gather_rules.py` (`Dock`), `tests/test_smoke_p1.py` | Đạt |
| AC-P1-07 Giỏ theo thứ tự nhặt, không vượt `hold_capacity` | Test luật | `tests/test_gather_rules.py` (`Hold`) | Đạt |

Phá thử `gather.py` theo 22 cách khác nhau (mô tả PR #7): cả 22 đều bị test bắt. Đối chiếu từng luật với PRD-0 mục F bằng cách đọc lab board; chưa có bộ test ẩn của giảng viên.

## B. Buổi tối: Mở Quán (`quan`)

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P1-08 Khách đến tick 120 rồi mỗi 900 tick, bàn trống id nhỏ nhất, hết bàn thì bỏ lượt, `no_dish` khi thiếu nguyên liệu | Test luật và test hộp đen | `tests/test_quan_slice3.py`, `tests/test_quan_rules.py` | Đạt |
| AC-P1-09 Giữ chỗ nguyên liệu: tồn trừ phần giữ, không giữ vượt kho (cả kho khai trong scenario và `--inventory`) | Test luật; scenario vượt kho thoát mã 2 | `tests/test_quan_slice3.py`, `tests/test_scenario_contract.py` (`ReservedVsInventory`) | Đạt |
| AC-P1-10 Kiên nhẫn 60 s: rời với `patience`, uy tín trừ `left_reputation_delta`, kẹp theo tuning | Test luật; bất biến trong ca dài | `tests/test_quan_slice3.py`, `tests/test_quan_rules.py` (`Invariants`) | Đạt |
| AC-P1-11 Bếp: nhận đơn cũ nhất, trừ kho, nấu đúng thời gian, `dish_ready`, `ready_ticks` tăng, món chín không bao giờ cháy (`burn_s` null) | Test luật và test hộp đen | `tests/test_quan_slice4.py`, `tests/test_quan_rules.py` (`NeverBurns`) | Đạt |
| AC-P1-12 Một `interact` mỗi bước, chọn theo (khoảng cách, bếp trước bàn, id); bưng cần tay trống; phục vụ đúng đơn; phục vụ đúng tick kiên nhẫn về 0 vẫn hợp lệ | Test luật | `tests/test_quan_slice4.py` (`Interact`, `Serving`) | Đạt |
| AC-P1-13 Boa `floor(giá × tip_rate)` khi còn ≥ 50% kiên nhẫn (tính chính xác), `paid`, tiền, `earned`, uy tín +`tip_reputation` kẹp trần | Test luật; ca trọn vẹn qua headless | `tests/test_quan_slice4.py` (`Serving`, `Payment`), `tests/test_quan_rules.py` (`OneDishShift`) | Đạt |
| AC-P1-14 Hết ca: khách đang ăn trả ngay, khách đang chờ rời với `closing` không trừ uy tín, rồi `quan_end` | Test luật và test hộp đen | `tests/test_quan_slice3.py`, `tests/test_quan_slice4.py` (`Closing`), `tests/test_quan_rules.py` (`ShiftEnd`) | Đạt |
| AC-P1-15 Điểm `earned + 100 × floor(reputation)` trong mọi snapshot và dòng `end` | Test hộp đen | `tests/test_quan_rules.py` | Đạt |

Chưa quyết: tiền tố id của khách ngẫu nhiên (đang dùng `C`); xem `docs/clarify.md` câu 6. Phá thử `quan.py` theo 34 cách (mô tả PR #10, #13, #16): cả 34 đều bị ít nhất một test bắt; riêng cách "giữ chỗ không trừ khỏi kho khả dụng" chỉ bị test trong tiến trình bắt vì contract P1 chỉ có một bàn.

## C. Test Contract v1.0 (headless, scenario, kho)

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P1-16 CLI: tham số bắt buộc, mã thoát 0 và 2, `--ticks 0`, `--mode day` bị từ chối ở v1.0 | Smoke hộp đen | `tools/smoke_phase1.py`, [smoke.md](../proof/phase-1/smoke.md), `tests/test_smoke_p1.py` | Đạt |
| AC-P1-17 Inputs: `frames`, kế thừa trường vắng, cạnh lên, sai kiểu thì mã 2 | Test đơn vị và smoke | `tests/test_python_starter_units.py`, `tests/test_smoke_p1.py` | Đạt |
| AC-P1-18 Scenario: giá trị mặc định của khách, payload món, đơn `assigned` và `unfulfillable`, khách `eating`, giữ chỗ khác công thức hoặc quá tồn, mâu thuẫn thì mã 2 trước khi ghi output | Test scenario và test headless | `tests/test_scenario_contract.py` | Đạt một phần |
| AC-P1-19 Tuning: dải hợp lệ của `game.contract.json` (bếp, bàn, uy tín, menu, điểm) | Test contract | `tests/test_scenario_contract.py` (`ContractKeys`) | Đạt |
| AC-P1-20 JSONL: snapshot tick 0, sự kiện rồi snapshot, dòng `end` cuối, làm tròn 3 chữ số | Smoke và test hộp đen | `tests/test_smoke_p1.py`, `tests/test_quan_rules.py`, smoke.md | Đạt |
| AC-P1-21 File kho: schema `items`, ghi đúng một lần khi có `gather_end`, không ghi khi chạm `--ticks`, bàn giao sang quán | Smoke mục G | `tools/smoke_phase1.py`, `tests/test_smoke_p1.py` | Đạt |
| AC-P1-22 Tất định: cùng seed, input và tham số thì JSONL và kho giống từng byte; ngẫu nhiên chỉ qua `Streams` | Smoke nhiều seed; thử chèn lỗi không tất định | [smoke.md](../proof/phase-1/smoke.md), `tools/check_determinism.py` | Đạt |

Phần "đạt một phần" của AC-P1-18: chưa quyết `dish_id` của khách có bắt buộc không (hiện không bắt buộc, chỉ đảm bảo không lỗi), và đơn `reserved` thiếu `reserved` (PRD cấp theo công thức) chưa kiểm khi thiếu kho.

## D. Giao diện và nhóm

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P1-23 Cửa sổ `chonoi.live` chạy cả hai buổi, HUD tối thiểu (thời gian, oxy, Máu, giỏ, kho, món, kiên nhẫn, tiền, uy tín) | Chạy máy chủ thật, gọi `/state`, `/input`, `/restart` | [live.md](../proof/phase-1/live.md), `tests/test_live.py` | Đạt một phần: API và trường dữ liệu đã kiểm; chưa xem hình vẽ trên trình duyệt, đồ họa thật là Phase 2 |
| AC-P1-24 `TEAM.md` đủ thành viên, `team_size` khớp | `python tools/check_team.py`, `tests/test_team_check.py` | `TEAM.md`, `game.contract.json` | Đạt một phần: danh sách khớp, nhưng 2 commit của Tú gắn với tài khoản GitHub `HoAnhTu245` trong khi `TEAM.md` ghi `TuHoAnh`; cần Tú xác nhận tài khoản |
| AC-P1-25 Mỗi người ≥ 3 commit có nội dung bằng tài khoản của mình | Đếm commit trên `main` theo tài khoản GitHub | D (`luongvh2510`): 19; A (`NguyenDucNhat3006`): 5; B: 2 (tài khoản `HoAnhTu245`); C (`Cuongngucuteee`): 1 | **Chưa đạt** với B và C |
| AC-P1-26 Ghi chép: `docs/members/<handle>.md`, `ai-usage-log.md`, `standup.md`, `clarify.md` | Kiểm file | `docs/clarify.md` có 2 dòng của A; PR #3 thêm 6 dòng; hồ sơ cá nhân, nhật ký AI và standup còn trống | **Chưa đạt** |
| AC-P1-27 `AGENTS.md` có lệnh thật và tối thiểu 2 skill hoặc hook của nhóm | Đọc `AGENTS.md`, chạy từng công cụ | Skill `check-determinism`, hook `protect_locked_files`, hook `pre-push` (PR #14 thêm skill `check-no-hardcode`); `tests/test_agent_harness.py` | Đạt |
| AC-P1-28 Gắn tag `phase-1` trên nhánh chính chạy được | `git tag`, chạy test tại tag | Chưa gắn (việc P1-14) | **Chưa đạt** |

## Đánh giá ngắn

- **Đạt:** toàn bộ luật lõi của gather và quán, Test Contract v1.0 (CLI, inputs, scenario, JSONL, kho, mã thoát), tính tất định. 157 test xanh, smoke 27/27, nhiều đợt phá thử luật đều bị test bắt.
- **Đạt một phần:** kiểm scenario (AC-P1-18), giao diện live chưa xem bằng mắt (AC-P1-23), danh sách nhóm (AC-P1-24).
- **Chưa đạt:** số commit của B và C (AC-P1-25), hồ sơ cá nhân, nhật ký AI, standup (AC-P1-26), tag `phase-1` (AC-P1-28).
- **Hạn chế chung:** đối chiếu PRD-0 bằng cách đọc lab board, không có bộ test ẩn của giảng viên nên mức "đạt" là theo hiểu biết của nhóm; id khách ngẫu nhiên (`C`) chưa có xác nhận.
- **Cần chỉnh cho phase sau:**
  1. Mỗi người đưa hồ sơ, nhật ký AI và standup vào repo, và có đủ commit bằng đúng tài khoản trước khi tag.
  2. Quyết định `dish_id` bắt buộc hay không và hỏi PO về tiền tố id khách (câu 6 trong `clarify.md`).
  3. Bước chuyển sang `day` ở Phase 2 phải giữ nguyên hai chế độ độc lập và kiểm `invuln_ticks` theo `contract_version`.
  4. Không để một người ôm nhiều việc: D đã làm thay P1-10 và P1-15; chia lại ngay từ đầu Phase 2.
