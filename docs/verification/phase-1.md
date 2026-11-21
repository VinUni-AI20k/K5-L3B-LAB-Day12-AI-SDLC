# Ma trận truy vết Phase 1

Nguồn yêu cầu: PRD-0 + Test Contract v1.0 (chép tại [`docs/contracts/test-contract-v1.md`](../contracts/test-contract-v1.md)).
Bằng chứng tái tạo được từ gốc repo: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` và
`bash docs/proof/phase-1/run_proof.sh`. Kết quả thật lưu ở [`docs/proof/phase-1/`](../proof/phase-1/).

> Bằng chứng hiện chạy trên working tree **chưa commit** (base `f0a1906`, xem dòng đầu `proof.txt`). Khi gắn tag
> `phase-1`, Integrator chạy lại hai lệnh trên ở commit gắn tag và cập nhật hai file `unittest.txt`, `proof.txt`.

| AC | Yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P1-01 | `dive`/`surface` khi đổi phía biên mặt nước (d ≤ 0.5), data `pos` sau di chuyển | `test_gather_p1.test_ac_p1_01_*` | [unittest.txt](../proof/phase-1/unittest.txt), [full-gather.events.jsonl](../proof/phase-1/full-gather.events.jsonl) | đạt |
| AC-P1-02 | Oxy theo d cuối bước: dưới nước −1, mặt nước +6 kẹp tối đa | `test_ac_p1_02_*` | unittest.txt | đạt |
| AC-P1-03 | `oxygen_empty` khi từ dương về 0; ngạt đầu tiên ở t+59, mỗi 60 tick −1 Máu (`choke`) | `test_ac_p1_03_*` | unittest.txt | đạt |
| AC-P1-04 | Máu 0 → bỏ giỏ LIFO, `faint` → `gather_end fainted` kho rỗng, file kho `{"items":{}}` | `test_ac_p1_04_*` | unittest.txt | đạt |
| AC-P1-05 | Nổi lên đúng bước đáng lẽ ngạt thì hồi oxy, không ngạt | `test_ac_p1_05_*` | unittest.txt | đạt |
| AC-P1-06 | Chặn biên từng thành phần, triệt vận tốc hướng ra ngoài | `test_ac_p1_06_*` | unittest.txt | đạt |
| AC-P1-07 | Hái nút đúng mép bán kính (tính cả mép), `regrow_ticks = 1200` | `test_ac_p1_07_*` (đúng fixture ví dụ mục D) | unittest.txt | đạt |
| AC-P1-08 | Nút gần nhất, hòa theo khóa id (`N2` trước `N10`) | `test_ac_p1_08_*` | unittest.txt | đạt |
| AC-P1-09 | Chỉ hái ở mặt nước; giỏ đầy → `hold_full` (required, free), nút giữ nguyên | `test_ac_p1_09_*` | unittest.txt | đạt |
| AC-P1-10 | Nút 1→0 phát `node_regrown` và hái được ngay cùng bước | `test_ac_p1_10_*` | unittest.txt | đạt |
| AC-P1-11 | Bắt đàn gần nhất trong bán kính (cả mép), thêm **toàn bộ** yield, xóa đàn, cooldown 30 tick | `test_ac_p1_11_*` | unittest.txt | đạt |
| AC-P1-12 | Cooldown L đặt ở t dùng lại từ t+L (bấm ở bước 29 trượt, bước 30 bắt được, event tick 31) | `test_ac_p1_12_*` | unittest.txt | đạt |
| AC-P1-13 | Thiếu chỗ khi bắt → `hold_full`, giữ đàn, không đặt cooldown | `test_ac_p1_13_*` | unittest.txt | đạt |
| AC-P1-14 | Bắt ở mặt nước / ngoài tầm: không event, không cooldown | `test_ac_p1_14_*` | unittest.txt | đạt |
| AC-P1-15 | Hết giờ ở mọi độ sâu → `gather_end time`, giữ giỏ, file kho khớp `inventory` | `test_ac_p1_15_*` | unittest.txt | đạt |
| AC-P1-16 | Chạm `--ticks` trước khi xong buổi sáng: `end.reason = tick_limit`, không ghi file kho | `test_ac_p1_16_*` | unittest.txt | đạt |
| AC-P1-17 | Cập bến xét trước hái, theo khoảng cách tới tâm bến trên `[x,d]` | `test_ac_p1_17_*`, smoke | unittest.txt, [proof.txt](../proof/phase-1/proof.txt) | đạt |
| AC-P1-18 | 6 đàn mặc định đứng yên, bắt được bằng preset | `test_ac_p1_18_*`, lượt đầy đủ | unittest.txt, proof.txt | đạt |
| AC-P1-20 | Khách đầu tiên ở `first_customer_tick` = 120, giữ chỗ đúng công thức, kiên nhẫn giảm từ bước sau | `test_quan_p1.test_ac_p1_20_*` | unittest.txt | đạt |
| AC-P1-21 | Không món nào đủ nguyên liệu khả dụng → `no_dish {}` | `test_ac_p1_21_*` | unittest.txt, full-quan.events.jsonl | đạt |
| AC-P1-22 | Không còn bàn trống → bỏ lượt khách | `test_ac_p1_22_*` | unittest.txt | đạt |
| AC-P1-23 | Hết kiên nhẫn → `customer_left patience`, uy tín −0.5, nhả phần giữ | `test_ac_p1_23_*` | unittest.txt | đạt |
| AC-P1-24 | Chọn món theo seed (Streams), cùng seed → byte giống nhau | `test_ac_p1_24_*`, `cmp` trong proof | unittest.txt, proof.txt | đạt |
| AC-P1-30 | Nấu → chín → bưng: `cook_started` (items, base_price), `dish_ready`, `dish_picked` | `test_ac_p1_30_*` | unittest.txt | đạt |
| AC-P1-31 | Phục vụ đúng đơn, boa `floor(giá × 0.2)`, ăn 600 tick rồi `paid finished_eating`, uy tín +0.2, điểm | `test_ac_p1_31_*` | unittest.txt | đạt |
| AC-P1-32 | Ngưỡng boa dùng kiên nhẫn **sau bước 1** (1800/3600 = 0.5 → có boa) | `test_ac_p1_32_*` | unittest.txt | đạt |
| AC-P1-33 | Sai đơn / tay trống tại bàn: bỏ lượt | `test_ac_p1_33_*` | unittest.txt | đạt |
| AC-P1-34 | Tối đa một interact, chọn (khoảng cách, bếp trước bàn, id) | `test_ac_p1_34_*` | unittest.txt | đạt |
| AC-P1-35 | Khách rời → bỏ món của đơn trên bếp/tay | `test_ac_p1_35_*` | unittest.txt | đạt |
| AC-P1-36 | Hết ca: khách đang ăn trả `closing`, khách chờ rời `closing` không trừ uy tín, rồi `quan_end` | `test_ac_p1_36_*` | unittest.txt | đạt |
| AC-P1-37 | Uy tín kẹp `[0, 5]` | `test_ac_p1_37_*` | unittest.txt | đạt |
| AC-P1-38 | Quán đọc file kho: tiền/earned = 0, uy tín theo tuning | `test_ac_p1_38_*` | unittest.txt | đạt |
| AC-P1-39 | Fixture mâu thuẫn mục D → mã 2, không ghi đầu ra | `test_ac_p1_39_*` (9 ca) | unittest.txt | đạt (chưa phủ hết mọi ca liệt kê ở D, xem "chưa đạt") |
| AC-P1-40 | Đơn reserved thiếu `reserved` → cấp theo công thức, thiếu hàng → `unfulfillable` | `test_ac_p1_40_*` | unittest.txt | đạt (theo giả định C-04) |
| AC-P1-41 | **Smoke hai tiến trình**: gather `--inventory-out` → quán `--inventory`, snapshot tick 0 `stock {"bong_sung":2,"ca_loc":1}` | `test_ac_p1_41_*`, `run_proof.sh` | proof.txt (`SMOKE OK`), [catch.json](../proof/phase-1/catch.json), [smoke-quan.jsonl](../proof/phase-1/smoke-quan.jsonl) | đạt |
| AC-P1-42 | Chơi trọn hai buổi 10800 tick nối qua file kho | `make_inputs.py` (bot) → `run_proof.sh` | proof.txt: gather `docked` 10 món; quán `time`, 3 món phục vụ, earned 264, điểm 564 | đạt |
| AC-P1-43 | Test chạy bằng 1 lệnh, xanh | lệnh test ở trên | unittest.txt: 67 test OK | đạt |
| DoD | HUD đọc được trong lúc chơi | `chonoi.live` (khung) + `client/` (GUI nhóm) | — | chưa kiểm ở bản này (QA chơi thử trước khi tag) |
| DoD | Tag `phase-1` trên `main`, commit theo tài khoản từng người | git | — | chưa làm (chờ nhóm commit theo lát + Integrator gắn tag) |

## Đánh giá ngắn
- Đạt: toàn bộ luật lõi gather (lát 1–2) và quán (lát 3–4) theo mục F; smoke hộp đen mục G; tất định byte.
- Chưa đạt / chưa kiểm: HUD trong lúc chơi chưa được QA xác nhận ở bản này; kiểm mâu thuẫn fixture mục D chưa đủ
  mọi ca (ví dụ `order_tick` lớn hơn phase hiện tại, vị trí bếp/bàn ngoài miền); `--snapshot-every`/`phase_tick`
  vẫn dùng chung bộ đếm tick ngoài vì Phase 1 chỉ có một pha mỗi lượt.
- Điều cần chỉnh cho phase sau: nếu v1.1 có `--mode day` thì `sim_tick`/`phase_tick` phải tách khỏi `tick` trong `runner.py`.
