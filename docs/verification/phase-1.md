# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-P1-01 | `dive`/`surface` phát đúng khi qua biên `d = 0.5`, data `pos` | `test_gather_lat1.py` (DiveSurface) / [test-results.txt](file:///c:/Users/Gigabyte/OneDrive/Máy tính/K5-L3B-LAB-Day12-AI-SDLC-HKT/docs/proof/phase-1/test-results.txt) | Đạt |
| AC-P1-02 | Oxy: mặt nước +6 kẹp max, dưới nước −1 kẹp 0 | `test_gather_lat1.py` (Oxygen) / [test-results.txt](file:///c:/Users/Gigabyte/OneDrive/Máy tính/K5-L3B-LAB-Day12-AI-SDLC-HKT/docs/proof/phase-1/test-results.txt) | Đạt |
| AC-P1-03 | `oxygen_empty` đúng một lần khi từ dương xuống 0 | `test_gather_lat1.py` (Oxygen) / [test-results.txt](file:///c:/Users/Gigabyte/OneDrive/Máy tính/K5-L3B-LAB-Day12-AI-SDLC-HKT/docs/proof/phase-1/test-results.txt) | Đạt |
| AC-P1-04 | Ngạt: choke đầu ở t+59, mỗi 60 tick −1 Máu; nổi lên đúng bước đó thì không ngạt; `zero_oxy_ticks` reset khi ở mặt nước | `test_gather_lat1.py` (Choke) / [test-results.txt](file:///c:/Users/Gigabyte/OneDrive/Máy tính/K5-L3B-LAB-Day12-AI-SDLC-HKT/docs/proof/phase-1/test-results.txt) | Đạt |
| AC-P1-05 | Máu 0 → `faint` (`lost` LIFO) → `gather_end fainted`, kho rỗng, dừng bước | `test_gather_lat1.py` (Faint) / [test-results.txt](file:///c:/Users/Gigabyte/OneDrive/Máy tính/K5-L3B-LAB-Day12-AI-SDLC-HKT/docs/proof/phase-1/test-results.txt) | Đạt |
| AC-P1-06 | Giỏ LIFO, trần `hold_capacity` | `test_gather_lat1.py`, `test_gather_lat2.py` / [test-results.txt](file:///c:/Users/Gigabyte/OneDrive/Máy tính/K5-L3B-LAB-Day12-AI-SDLC-HKT/docs/proof/phase-1/test-results.txt) | Đạt |
| AC-P1-07 | Hái: nút `ready` gần nhất, hòa id nhỏ, đúng mép bán kính; `regrow_ticks = 1200`; `node_regrown` sau 1200 bước | `test_gather_lat2.py` (GatherInteract) / [test-results.txt](file:///c:/Users/Gigabyte/OneDrive/Máy tính/K5-L3B-LAB-Day12-AI-SDLC-HKT/docs/proof/phase-1/test-results.txt) | Đạt |
| AC-P1-08 | `hold_full` khi hái thiếu chỗ, nút giữ nguyên | `test_gather_lat2.py` (GatherInteract) / [test-results.txt](file:///c:/Users/Gigabyte/OneDrive/Máy tính/K5-L3B-LAB-Day12-AI-SDLC-HKT/docs/proof/phase-1/test-results.txt) | Đạt |
| AC-P1-09 | Bắt cá: đúng đàn gần nhất, yield đủ (`ca_linh` 3, `ca_loc` 1), cooldown 30 tick | `test_gather_lat2.py` (CatchFish) / [test-results.txt](file:///c:/Users/Gigabyte/OneDrive/Máy tính/K5-L3B-LAB-Day12-AI-SDLC-HKT/docs/proof/phase-1/test-results.txt) | Đạt |
| AC-P1-10 | `catch` thiếu chỗ: `hold_full`, giữ đàn, không cooldown, không nhận một phần | `test_gather_lat2.py` (CatchFish) / [test-results.txt](file:///c:/Users/Gigabyte/OneDrive/Máy tính/K5-L3B-LAB-Day12-AI-SDLC-HKT/docs/proof/phase-1/test-results.txt) | Đạt |
| AC-P1-11 | `catch` ở mặt nước hoặc không có đàn: không event, không cooldown | `test_gather_lat2.py` (CatchFish) / [test-results.txt](file:///c:/Users/Gigabyte/OneDrive/Máy tính/K5-L3B-LAB-Day12-AI-SDLC-HKT/docs/proof/phase-1/test-results.txt) | Đạt |
| AC-P1-12 | Cập bến xét trước hái; `docked` ghi đúng giỏ; ngất ghi `{"items":{}}` | `test_gather_lat2.py` (DockAndTimeout), [gather-smoke.jsonl](file:///c:/Users/Gigabyte/OneDrive/Máy tính/K5-L3B-LAB-Day12-AI-SDLC-HKT/docs/proof/phase-1/gather-smoke.jsonl), [gather-inventory.json](file:///c:/Users/Gigabyte/OneDrive/Máy tính/K5-L3B-LAB-Day12-AI-SDLC-HKT/docs/proof/phase-1/gather-inventory.json) | Đạt |
| AC-P1-13 | Hết giờ `time` giữ giỏ; kho ghi đúng một lần, nguyên tử; chạm `--ticks` thì không ghi | `test_smoke_p1.py` (Integration/Movement), `test_gather_lat2.py` (DockAndTimeout) | Đạt |
| AC-P1-14 | Tất định: cùng seed/tham số/input → JSONL + kho giống từng byte | `test_smoke_p1.py` (Contract.test_con_02_deterministic_bytes) + SHA256 kiểm tra | Đạt |
| AC-P1-15 | Snapshot/event đúng schema mục E (kể cả `hold_count`, `at_surface`, `oxygen_max_ticks`, `hp_max`) | `test_smoke_p1.py` (Contract.test_gather_snapshot_has_gather_fields) | Đạt |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt: Toàn bộ 15 AC của Phase 1 phần Gather (lát 1 và lát 2) đều ĐẠT.
- Điều cần chỉnh cho phase sau: Chuẩn bị cơ chế di chuyển / sinh thêm của cá cho Phase 2 (nếu có yêu cầu từ PRD-2).
