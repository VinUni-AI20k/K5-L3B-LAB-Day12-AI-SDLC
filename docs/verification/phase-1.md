# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-P1-01 | Smoke hợp đồng kho và schema | `tests/test_smoke_p1.py::Integration`, `docs/proof/phase-1/qa-baseline.txt` | đạt |
| AC-P1-02 | Event oxy rỗng, ngạt/choke dưới nước | `tests/test_qa_phase1.py::GatherContract`, `tests/test_gather_lat1.py` | đạt |
| AC-P1-03 | Hái nút và hold_full | `tests/test_qa_phase1.py::GatherContract`, `tests/test_gather_lat2.py` | đạt |
| AC-P1-04 | Smoke gather ghi kho, quan đọc kho tick 0; smoke hai tiến trình trên `main` (`python3 tools/smoke_proof.py --phase phase-1`, 7 mục kiểm) | `tests/test_smoke_p1.py::Integration.test_inv_01_gather_writes_inventory_quan_reads_it`, [`docs/proof/phase-1/smoke.md`](../proof/phase-1/smoke.md) (commit `454b2eb`, 7/7) | đạt |
| AC-P1-05 | Khách đến theo lịch và giữ chỗ | `tests/test_qa_phase1.py::QuanContract.test_ac_p1_05_customer_arrives_and_reserves_inventory`, `tests/test_quan_lat3.py` | đạt |
| AC-P1-06 | Nấu, bưng, phục vụ, trả tiền | `tests/test_qa_phase1.py::QuanContract.test_ac_p1_06_cook_pick_serve_and_paid`, `tests/test_quan_lat4.py` | đạt |
| AC-P1-07 | HUD đọc được trong lúc chơi: `python3 tools/hud_check.py --phase phase-1` — 5 trạng thái do sim sinh ra (lặn, khách vừa đến, bếp nấu, cầm món, khách ăn) × 4 bề rộng 1280/900/700/480: không lỗi vẽ, không chữ đè/tràn, đủ trường HUD tối thiểu DoD (thời gian, oxy, Máu, giỏ; kho khả dụng, món gọi + kiên nhẫn, bếp, tay, tiền, uy tín), kho khả dụng = tồn − giữ chỗ. Công cụ đã thử trên HUD gốc `e5700a3` → CHƯA ĐẠT 31/57 (bắt được lỗi). `test_live` kiểm server trình duyệt | [`docs/proof/phase-1/hud.md`](../proof/phase-1/hud.md) (commit `10db256`, 57/57), `tests/test_live.py` | đạt (tự động); chơi thử tay trên trình duyệt: người chơi tự ghi thêm nếu có |
| AC-P1-08 | Test bằng một lệnh; clone sạch chạy trong ≤ 3 lệnh theo README: `git clone` từ GitHub ở commit `70120ca` → `python -m chonoi.live --mode gather` trả HTTP 200, `unittest discover` toàn bộ OK | `README.md` (mục "Nhóm nhom6ae — chạy game"), lệnh test trong `AGENTS.md` | đạt — kiểm trên Windows bằng `python` (máy không có `python3`); chưa chạy thử trên macOS/Linux |

## Đánh giá ngắn
- Yêu cầu đã kiểm đạt: AC-P1-01 đến AC-P1-06; full suite 70/70 pass. AC-P1-07 đạt bằng kiểm HUD tự động (57/57).
- Chưa xác minh: chạy README trên macOS/Linux (đã kiểm clone sạch trên Windows).
- Điều cần chỉnh cho phase sau: tag `phase-1` gắn sau mốc 1:00 (Phase 2 đã mở); mỗi người còn thiếu file phản tư `docs/members/<handle>.md`; luôn chạy cả bộ test sau khi gỡ conflict (sự cố nhánh `chuan`).
