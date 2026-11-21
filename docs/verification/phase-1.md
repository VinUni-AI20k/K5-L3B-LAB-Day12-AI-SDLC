# Ma trận truy vết Phase 1

Đối chiếu PRD-0 và Test Contract v1.0 ngày 2026-11-21. Các mã AC dưới đây dùng để truy vết trong repo. Bản `main` tại `fdc986b` đạt 45/45 test. Bản bàn giao đang làm việc trên `lam` từ `a1e7277` đạt **48/48 test** và smoke Chrome. [Bằng chứng tích hợp](../proof/phase-1/ban-giao.md)

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P1-01 · Gather chơi được, có bơi, oxy, Máu, hái và bắt | Fixture kiểm chặn mép, oxy/ngạt, giỏ đầy, hồi nút và hành động bước cuối | [Gather](../proof/phase-1/gather.md), [QA](../proof/phase-1/qa.md) | Đạt các ca đã chạy |
| AC-P1-02 · Cập bến/hết giờ giữ giỏ, ngất chốt kho rỗng | Kiểm event theo tick, thứ tự LIFO và nội dung kho | [Gather](../proof/phase-1/gather.md), [test QA](../../tests/test_qa_phase1.py) | Đạt |
| AC-P1-03 · Quán xử lý khách, giữ chỗ, phục vụ và thu tiền | Test khách đến, thiếu món, nấu → bưng → phục vụ → trả tiền, kiên nhẫn và đóng ca | [Quán](../proof/phase-1/quan-sim.md), [test Quán](../../tests/test_quan.py) | Đạt các ca đã chạy |
| AC-P1-04 · Tick và lỗi fixture theo Test Contract | Test snapshot tick 0 và tick dừng, JSONL tất định, fixture sai trả mã 2 trước khi ghi. Kiểm lịch khách khi rút ngắn ca và dọn đơn ở tick biên | [Bằng chứng tích hợp](../proof/phase-1/ban-giao.md), [smoke công khai](../../tests/test_smoke_p1.py) | Đạt các ca đã chạy |
| AC-P1-05 · Gather → file kho → Quán | `python3 tools/phase1.py smoke` chạy hai tiến trình seed 42 và đối chiếu kho tại tick 0 của Quán | [Bằng chứng tích hợp](../proof/phase-1/ban-giao.md) | Đạt |
| AC-P1-06 · Điều khiển, HUD và demo trình duyệt | Chrome chạy menu → Gather → E tại bến → mở Quán. Kiểm HUD oxy, file kho và HUD kho khả dụng | [Bằng chứng tích hợp](../proof/phase-1/ban-giao.md), [bằng chứng UI](../proof/phase-1/client-ui.md) | Đạt |
| AC-P1-07 · README, hợp đồng tích hợp và TEAM | Kiểm lệnh chạy và test, phím, điểm, schema kho, số người và handle đối chiếu bốn PR đã gộp | [README](../../README.md), [giao diện](../../TEAM.md#giao-diện-dùng-chung), [kho mẫu](../contracts/inventory.sample.json) | Đạt cho các mục đã kiểm |
| AC-P1-08 · Ghi chép nhóm và cá nhân | Đối chiếu clarify, nhật ký AI, retro và hồ sơ đóng góp theo GitHub handle | [Clarify](../clarify.md), [nhật ký AI](../ai-usage-log.md), [retro](../retro.md), [thành viên](../members/) | Còn xác nhận phản tư cá nhân và dữ liệu AI chưa ghi |
| AC-P1-09 · Tag bàn giao trên `main` | Kiểm tag local và `git ls-remote --tags origin refs/tags/phase-1` | [Bằng chứng tích hợp](../proof/phase-1/ban-giao.md) | Chưa có tag `phase-1` khi kiểm |

## Đánh giá ngắn

- Suite, smoke hai tiến trình và kiểm trình duyệt đều đạt trên bản bàn giao đã kiểm. Kết quả áp dụng cho các fixture và test trong repo.
- Trước mốc Phase 2, giữ phép kiểm với thời lượng ca rút ngắn, hai timer chạm 0 cùng tick và fixture sai phải bảo toàn đầu ra.
