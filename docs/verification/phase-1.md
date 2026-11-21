# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| `AC-P1-01` | Chạy test hợp đồng `--ticks 0`, deterministic bytes, mã thoát 2 và kiểm dải `game.contract.json` (`Contract`, `ScenarioModes`, `ContractTuningRangesTest`) | [`unittest-output.txt`](../proof/phase-1/unittest-output.txt) | **Đạt** (36/36 test pass) |
| `AC-P1-02` | Chạy test bơi, `ramp_max_ticks`, hướng `heading_deg`, chặn biên & triệt vận tốc ở mép (`Movement`) | [`unittest-output.txt`](../proof/phase-1/unittest-output.txt) | **Đạt** |
| `AC-P1-03` | Kiểm tra `dive`/`surface`, hồi/trừ oxy và `oxygen_empty` | — | **Chưa đạt** — Lát 1 chưa kéo về nhánh local (đã thấy PR #1 trên `origin/main`, sẽ chạy lại `verify-ac` sau khi `git pull`) |
| `AC-P1-04` | Kiểm tra ngạt (`choke` ở t+59), Máu 0 → `faint` (mất giỏ LIFO, kho rỗng) | — | **Chưa đạt** — Lát 1 chưa kéo về nhánh local (đã thấy PR #1 trên `origin/main`, sẽ chạy lại `verify-ac` sau khi `git pull`) |
| `AC-P1-05` | Kiểm tra hái nút mặt nước (`gather`, `regrow_ticks`, `node_regrown`), `hold_full` | — | **Chưa đạt** — chờ B hoàn thiện và merge Lát 2 |
| `AC-P1-06` | Kiểm tra bắt cá dưới nước (`catch`, `fish_caught`, xóa đàn, hồi chiêu, `hold_full`) | — | **Chưa đạt** — chờ B hoàn thiện và merge Lát 2 |
| `AC-P1-07` | Kiểm tra cập bến (`docked`), hết giờ (`time`) giữ giỏ, ghi kho 1 lần nguyên tử | [`unittest-output.txt`](../proof/phase-1/unittest-output.txt), [`smoke-2proc-log.txt`](../proof/phase-1/smoke-2proc-log.txt) | **Đạt một phần** — khung cập bến/hết giờ/ghi kho 1 lần đạt; chờ ghép hái & bắt cá của Lát 2 |
| `AC-P1-08` | Chạy smoke hộp đen 2 tiến trình (`gather --inventory-out` → `quan --inventory`) và test tích hợp `Integration`, `SmokeTwoProcessExtraTest` | [`smoke-2proc-log.txt`](../proof/phase-1/smoke-2proc-log.txt), [`catch.json`](../proof/phase-1/catch.json), [`dock.json`](../proof/phase-1/dock.json), [`dock-inputs.json`](../proof/phase-1/dock-inputs.json), [`unittest-output.txt`](../proof/phase-1/unittest-output.txt) | **Đạt** (`quan` tick 0 đọc đúng `{"bong_sung":2,"ca_loc":1}`) |
| `AC-P1-09` | Kiểm tra khách theo lịch (`first_customer_tick`, `customer_interval_s`), chọn món từ kho khả dụng, giữ chỗ, `no_dish` | — | **Chưa đạt** — Lát 3 chưa kéo về nhánh local (đã thấy commit của C trên `origin/main`, sẽ chạy lại `verify-ac` sau khi `git pull`) |
| `AC-P1-10` | Kiểm tra giảm kiên nhẫn, khách bỏ đi (`patience`/`closing`), nhả giữ chỗ & kiểm mâu thuẫn `scenario.py` (mã 2) | — | **Chưa đạt** — Lát 3 chưa kéo về nhánh local (đã thấy commit của C trên `origin/main`, sẽ chạy lại `verify-ac` sau khi `git pull`) |
| `AC-P1-11` | Kiểm tra tương tác quán: nấu (`cook_started` → `dish_ready`), bưng (`dish_picked`), phục vụ (`served`) | — | **Chưa đạt** — chờ D hoàn thiện và merge Lát 4 |
| `AC-P1-12` | Kiểm tra ăn xong trả tiền (`paid`), boa, uy tín/điểm, dọn ca (`quan_end`) | — | **Chưa đạt** — chờ D hoàn thiện và merge Lát 4 |
| `AC-P1-13` | Kiểm tra `chonoi.live` phục vụ HUD 2 buổi (`drawGather`, `drawQuan`, kho khả dụng, tên món, assets cá) (`LiveServerTest`, `LiveHudAndAssetsTest`) | [`unittest-output.txt`](../proof/phase-1/unittest-output.txt) | **Đạt** (server + HUD + assets test pass) |
| `AC-P1-14` | Kiểm tra DoD & quy trình (`tools/check_team.py`, 2 skill `.agents/skills/`, `docs/plan/phase-1.md`, `README.md`, `CREDITS.md`, `docs/ai-usage-log.md`, tag `phase-1`) | [`check-team-output.txt`](../proof/phase-1/check-team-output.txt), [`unittest-output.txt`](../proof/phase-1/unittest-output.txt) | **Chưa đạt** — đã hoàn tất 2 skill, `docs/plan/phase-1.md`, `README.md`, `CREDITS.md` (chờ điền link nguồn gói `assets/fish/`), dòng nhật ký AI của E và bằng chứng bước đầu; còn chờ B điền `TEAM.md` (`check_team.py` thoát mã 1), nhật ký AI các thành viên còn lại, và A gắn tag `phase-1` |

## Đánh giá ngắn
- **Yêu cầu nào đạt / chưa đạt:** Trên bản local hiện tại, bộ test 36/36 case (`test_smoke_p1.py`, `test_python_starter_units.py`, `test_live.py`, `test_team_check.py`, `test_e_qa_p1.py`), smoke hộp đen 2 tiến trình (`gather` → `quan`), hợp đồng kho, HUD `chonoi/web/index.html`, `README.md` và 2 skill đã **Đạt**. Các tiêu chí `AC-P1-03..06`, `AC-P1-09..12` và `AC-P1-14` tạm **Chưa đạt** trên local vì nhánh hiện tại chưa `git pull` Lát 1 & Lát 3 từ `origin/main`, Lát 2 & Lát 4 chưa merge, `TEAM.md` chưa điền đủ 5 thành viên và `CREDITS.md` còn chờ điền link nguồn gói `assets/fish/`.
- **Điều cần chỉnh cho phase sau / trước khi gắn tag `phase-1`:**
  1. Kéo `origin/main` (Lát 1, Lát 3, gộp dòng `docs/ai-usage-log.md` của A và E) và đợi merge Lát 2, Lát 4 cùng `TEAM.md` (5 thành viên).
  2. Điền tên tác giả, link nguồn và giấy phép CC0/CC-BY/MIT cho gói `assets/fish/` trong `CREDITS.md`; bổ sung nhật ký AI các thành viên còn lại.
  3. Chạy lại skill `smoke-p1` (kèm file kho thật từ lượt chơi của B) và `verify-ac` trên `main` ngay trước khi A gắn tag `phase-1`.
