# Ma trận truy vết Phase 1

> Chạy trên `main` sau khi gộp PR #3 (lát 1) và PR #1 (lát 2), cùng lát 3 đã có trên `main`. Commit kiểm chứng: `8645774`. Tag `phase-1` gắn trên commit chứa file này.
> Gắn **trễ hạn 1:00** (gắn trong giờ phase 2). Lát 4 (PR #2) chưa gộp vì làm trượt test lát 3 (xem cuối file).
> Tổng: `unittest` 88/88 OK ([unittest.txt](../proof/phase-1/unittest.txt)) · smoke 10/10 ([smoke.txt](../proof/phase-1/smoke.txt)) · tất định 12/12 ([tat-dinh.txt](../proof/phase-1/tat-dinh.txt)).

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-P1-01 | `game.contract.json` đủ khóa preset v1.0, `team`/`team_size` = 5; `contract.py` kiểm khi chạy headless; `tools/check_team.py` | [unittest.txt](../proof/phase-1/unittest.txt) (`test_team_check`, `test_smoke_p1`) | đạt |
| AC-P1-02 | Hợp đồng kho + sự kiện + giao diện ở `docs/contracts/README.md`, ví dụ `inventory.sample.json` | [smoke.txt](../proof/phase-1/smoke.txt) (ví dụ trong hợp đồng chạy đúng) | đạt |
| AC-P1-03 | README: chạy từ clone sạch 3 lệnh, điều khiển, điểm, lệnh test | `README.md` (đọc lại) | đạt (chưa thử trên máy macOS/Linux sạch) |
| AC-P1-10 | `test_gather_core_movement` (ramp, chuẩn hóa chéo, giữ hướng, triệt vận tốc ở 4 mép) | [unittest.txt](../proof/phase-1/unittest.txt) | đạt |
| AC-P1-11 | `test_gather_survival`: `test_dive_surface_and_final_depth`, `test_no_transition_at_rest_and_initial_empty` | như trên | đạt |
| AC-P1-12 | `test_oxygen_depletion_refill_and_limits`, `test_dive_empty_and_faint_event_order_in_same_tick` | như trên | đạt |
| AC-P1-13 | `test_choke_exact_tick_and_repeat` (ngạt ở t+59), `test_surface_on_due_tick_prevents_choke` | như trên | đạt |
| AC-P1-14 | `test_faint_lifo_order_final_snapshot_inventory_and_determinism` | như trên | đạt |
| AC-P1-15 | `test_hold_full_khi_hai`, `test_hold_full_khong_thu_dan_khac`, `lost` LIFO khi ngất | như trên | đạt |
| AC-P1-20 | `test_gather_slice2::Harvest` (đúng mép bán kính, gần nhất hòa id, chỉ mặt nước, `node_regrown`, bến xét trước) | như trên | đạt |
| AC-P1-21 | `Catch` (bắt thành công, hòa id, hồi chiêu đúng tick, thiếu chỗ không thử đàn khác, mặt nước không bắt) | như trên | đạt |
| AC-P1-22 | `EndAndInventory`: hái / bắt ở bước cuối vẫn vào kho | như trên | đạt |
| AC-P1-23 | `test_docked_ghi_kho_dung_noi_dung`, `test_cham_ticks_truoc_khi_xong_khong_ghi`; smoke mục 2, 4 | như trên + [smoke.txt](../proof/phase-1/smoke.txt) | đạt |
| AC-P1-30 | `tests/test_quan_customers.py::Schedule` (khách ở tick 120, +900, bàn id nhỏ nhất, hết bàn bỏ lượt, chạy qua headless) | [lat3-quan-customers.txt](../proof/phase-1/lat3-quan-customers.txt) | đạt (sự kiện theo hợp đồng mục 3) |
| AC-P1-31 | `DishChoice` (chỉ món đủ kho khả dụng, `no_dish {}`, luồng RNG `customers`, trừ phần đang giữ, cùng seed cùng món, 60 seed phủ đủ menu) | như trên | đạt |
| AC-P1-32 | `Reservation` (giữ đúng công thức, không trừ tồn, `_release` nhả giữ + bỏ món trên bếp/tay) | như trên | đạt |
| AC-P1-33 | `Patience` + `StepOrder` (rời ở tick 120+3600, `reason: patience`, uy tín −0.5, kẹp min, khách đang ăn không giảm; rời ở bước 4 sau interact nên phục vụ đúng tick kiên nhẫn 0 vẫn hợp lệ; hết ca → `closing` không trừ uy tín) | như trên | đạt |
| AC-P1-34 | `Fixture` (fixture hợp lệ → snapshot đúng; 21 kiểu mâu thuẫn → mã 2 (gồm assigned không có món, unfulfillable có món, eating sai giá, payload liên kết thiếu / không khớp đơn, bếp và tay cùng đơn, cooking timer 0); 4 fixture liên kết hợp lệ → mã 0; giữ chỗ quá kho `--inventory` → mã 2) | như trên | đạt |
| AC-P1-40 | Chọn một `interact` theo (khoảng cách, bếp trước bàn, id) | — | **chưa đạt**: PR #2 chưa gộp; bản PR chỉ xét bếp ready / bàn khớp món, không bỏ lượt khi đối tượng gần nhất không tương tác được |
| AC-P1-41 | Bếp idle + `interact` → `cook_started` → `dish_ready` | — | **chưa đạt**: PR #2 tự nấu mỗi bước, không cần `interact` (làm trượt 2 test lát 3) |
| AC-P1-42 | Bếp ready → tay trống, `dish_picked` | — | **chưa đạt** (PR #2 chưa gộp) |
| AC-P1-43 | `served`, boa, `paid finished_eating`, uy tín +0.2 | — | **chưa đạt** (PR #2 chưa gộp) |
| AC-P1-44 | Hết ca: khách ăn trả `closing`, khách chờ rời không trừ uy tín, `quan_end` | `Patience` (lát 3, phần khách chờ) | **chưa đạt một phần**: khách chờ rời `closing` đạt; trả tiền khách đang ăn thuộc lát 4 |
| AC-P1-45 | Điểm = earned + 100 × floor(uy tín) ở snapshot và `end` | [smoke.txt](../proof/phase-1/smoke.txt), `smoke-quan.jsonl` (score 300 với uy tín 3.0) | đạt ở công thức (runner); chưa có ca thu tiền thật vì thiếu lát 4 |
| AC-P1-50 | Smoke hai tiến trình `dock.json` → `kho.json` → quán tick 0 `stock:{"bong_sung":2,"ca_loc":1}` | [smoke.txt](../proof/phase-1/smoke.txt), `smoke-kho.json` | đạt |
| AC-P1-51 | `kiem_tat_dinh.py`: 2 lần cùng seed, 3 seed × 4 kịch bản, so byte JSONL + kho | [tat-dinh.txt](../proof/phase-1/tat-dinh.txt) | đạt |
| AC-P1-52 | Kho sai → mã 2 (smoke mục 5); scenario mâu thuẫn → mã 2 (`Fixture`); cờ/inputs sai (`test_python_starter_units`) | [smoke.txt](../proof/phase-1/smoke.txt), [unittest.txt](../proof/phase-1/unittest.txt) | đạt |
| AC-P1-53 | HUD buổi sáng/tối đọc được khi chơi (`chonoi.live`), PR #1 thêm kho khả dụng + trạng thái bếp | `chonoi/web/index.html` | **chưa kiểm chứng**: chưa chơi thử ghi lại ảnh/kết quả |

## Đánh giá ngắn
- **Đạt:** lát 1, 2, 3, hợp đồng kho, smoke hai tiến trình, tất định, mã 2 cho đầu vào sai.
- **Chưa đạt:** lát 4 (bếp, bưng, phục vụ, tiền: AC-P1-40…44). PR #2 tự bắt đầu nấu không qua `interact` và chọn đối tượng sai luật, nên làm trượt `test_available_excludes_reserved` và `test_reserved_released_on_patience_leave` của lát 3; đã review trên PR. HUD (AC-P1-53) chưa chơi thử. Tag gắn trễ hạn 1:00.
- **Điều cần chỉnh cho phase sau:** gộp nhánh sớm hơn (trước phút 45) và chạy test của lát khác trước khi mở PR; lát 4 sửa và gộp ở đầu phase 2, trước khi nâng contract v1.1; chơi thử HUD và lưu ảnh vào `docs/proof/`.
