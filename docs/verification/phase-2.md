# Ma trận truy vết Phase 2 — Test Contract v1.1

| Yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả hiện tại |
|---|---|---|---|
| Chuyển kho gather → quán | Seed 42, xuất kho khi cập bến, đối chiếu stock ở snapshot quán tick 0 | [Smoke tích hợp](../proof/phase-2/integration.md) | Đạt trên main tại 8c1d93c với nguyên liệu Phase 1. |
| Bàn giao nguyên liệu mới — `ca_keo`, `keo_neo` | Kiểm tra fixture giỏ gather rồi kiểm tra riêng quán nạp kho | [Bằng chứng](../proof/phase-2/integration.md) | Quán nạp trực tiếp đạt tại 9f4c078. Smoke hai tiến trình tại 8c1d93c bị chặn ở gather.hold, mã 2. |
| Mua oxy đúng giá, áp dụng từ Ngày kế | Chạy `day --days 2`, mua với đúng 200 tiền và kiểm tra oxy đầu Ngày 2 | [Test day/Shop](../../tests/test_qa_phase2.py) | Tại 8c1d93c, CLI từ chối --days 2. Chưa kiểm được luật mua và áp dụng nâng cấp. |
| Vòng ngày và kế hoạch D1–D5 | Smoke `day --days 1`, kiểm tra chuyển pha, kế hoạch và `days_completed` khi Shop đóng | — | Chưa chạy trên v1.1. |
| Pause | Kiểm tra đồng hồ và bộ đếm đứng yên khi pause; gameplay tiếp tục ngay ở bước resume | [Test pause](../../tests/test_qa_phase2.py) | Tại 8c1d93c, parser từ chối pause tại frame 0. Chưa kiểm được hành vi pause/resume. |
| Số liệu chuẩn, cá, Cá Sấu | Đối chiếu manifest và chạy fixture biên cho cá, Cá Sấu | — | Chưa chạy trên v1.1. |
| Regression Phase 1 | Chạy toàn bộ suite có sẵn trên nhánh quán, gồm smoke Phase 1 và hai ca QA Phase 1 | [Bằng chứng regression](../proof/phase-2/integration.md#kiểm-chứng-trên-nhánh-quán-phase-2) | Suite tích hợp tại 8c1d93c đạt 51/54. Ba lỗi xác thực đầu vào được ghi trong bằng chứng tích hợp. |
| Cá Sấu — Chạm làm ngất ở 1 Máu | Kiểm tra `monster_hit → faint → gather_end` trong cùng tick, hai lượt rơi đồ theo LIFO và kho rỗng | [Test Cá Sấu](../../tests/test_qa_phase2.py) | 	Ca gây ngất ở 1 Máu đạt tại 8c1d93c. Ca không gây ngất bị chặn khi kiểm tra gather.hold. |
| Quán mở rộng — 2 bếp, 4 bàn và 6 món | Chạy suite quán, gồm snapshot, món mới, thứ tự nhận đơn, lọc món theo kế hoạch và dọn ca | [Kết quả trên nhánh quán](../proof/phase-2/integration.md#kiểm-chứng-trên-nhánh-quán-phase-2) | 12/12 ca quán đạt trên main tại 8c1d93c. |
# Báo cáo nghiệm thu Phase 2

Kiểm ngày 2026-11-21 trên commit `881c4c41413115bc1bc99cc8d76bf7875b86576f`, trùng `main` trên GitHub khi kiểm. Manifest khai Test Contract `1.1`. Suite tích hợp đạt **51/54**, gồm **12/12 ca Quán** và toàn bộ suite hồi quy Phase 1. Smoke kho, hai mode headless độc lập và bản xem 5 ngày đều chạy được. Ba ca đỏ giữ trạng thái chưa đạt. [Kết quả và lệnh tái hiện](../proof/phase-2/integration.md#kiểm-chứng-trên-main-phase-2)

## Ma trận truy vết

| **Yêu cầu** | **Kiểm chứng trên bản tích hợp** | **Kết quả** |
|---|---|---|
| Gather mở rộng · cá di chuyển, phản xạ, sinh cá, sáu nút rau | Snapshot tick 0 có 8 đàn, 6 nút và 1 Cá Sấu. Ca phản xạ/sinh ở tick 360 và `random_fish: false` đều đạt. [Gather](../proof/phase-2/gather.md) | Đạt các ca đã chạy |
| Gather · va chạm Cá Sấu và thời gian bất tử | Fixture chứa `keo_neo` bị từ chối trước tick 0. Chạy đối chứng với `bong_dien_dien` có một lần trúng, rơi hai món LIFO và Máu `3 → 2 → 2`. [Bằng chứng](../proof/phase-2/integration.md#các-ca-chưa-đạt) | Chưa đạt fixture nguyên bản |
| Gather · đòn chí tử của Cá Sấu | Tick 1 có `monster_hit → faint → gather_end`; giỏ rơi theo LIFO, file kho rỗng. [Test QA](../../tests/test_qa_phase2.py) | Đạt |
| Quán mở rộng · 2 bếp, 4 bàn, 6 món | 12 ca qua snapshot, chọn bàn, món mới, thứ tự nhận đơn, lọc món theo `day_plan` trong `QuanSim`, phục vụ và dọn ca. [Test Quán](../../tests/test_quan.py) | Đạt |
| Gather → kho → Quán | Smoke seed 42, file khớp `gather_end.data.inventory`, Quán thấy `bong_sung: 2`, `ca_loc: 1` ở tick 0. [Smoke tích hợp](../proof/phase-2/integration.md) | Đạt |
| Tất định và hồi quy Phase 1 | Hai lần chạy seed 42, 600 tick cho từng mode độc lập tạo JSONL giống từng byte. `test_smoke_p1`, `test_qa_phase1`, `test_python_starter_units`, `test_live` và `test_team_check` đều đạt. [Bằng chứng tích hợp](../proof/phase-2/integration.md#kiểm-chứng-trên-main-phase-2) | Đạt các ca đã chạy |
| Vòng 5 ngày và `day_plan` · headless | Manifest có D1–D5. CLI trả mã 2 với `--mode day`, kể cả chạy riêng khi vắng `--days`. [Lệnh tái hiện](../proof/phase-2/integration.md#các-ca-chưa-đạt) | Chưa đạt |
| Shop · mua oxy giá 200, áp dụng từ ngày kế · headless | Test `day --days 2` trả mã 2 tại bước đọc cờ. Chưa quan sát được `bought` hoặc snapshot đầu Ngày 2 trong headless. [Test Shop](../../tests/test_qa_phase2.py) | Chưa đạt |
| Pause/resume · headless | Input `pause` bị từ chối ở frame 0. Chưa quan sát được việc dừng đồng hồ và chạy tiếp đúng bước. [Test pause](../../tests/test_qa_phase2.py) | Chưa đạt |
| UI · menu, HUD, cửa hàng và tổng kết | Bằng chứng Chrome trên nhánh UI bao phủ các màn và phím. Trên `881c4c4`, chạy lại adapter preview qua đủ D1–D5, đã kiểm pause và oxy mua Ngày 1 kích hoạt ở Ngày 2. [Bằng chứng UI](../proof/phase-2/client-ui.md), [lần chạy lại](../proof/phase-2/integration.md#ui-và-live-adapter) | Đạt trên snapshot mẫu |
| Campaign 5 ngày · live | `GET /config` hiện trả trực tiếp `tuning`, không có `contract_version` và `capabilities.campaign_v11`. Nút **Chơi** dùng adapter preview. [Bằng chứng live](../proof/phase-2/integration.md#ui-và-live-adapter) | Chưa nối campaign thật |
| Tag bàn giao trên `main` | Đối chiếu tag local và `git ls-remote` trên GitHub. [Kết quả](../proof/phase-2/integration.md#kiểm-chứng-trên-main-phase-2) | Chưa có `phase-2` lúc kiểm |

## Đóng góp của nhóm

| **Module** | **Người phụ trách** | **Phạm vi tích hợp** |
|---|---|---|
| `sim/gather` | Nguyễn Trung Dũng | Cá di chuyển và sinh theo chu kỳ, Cá Sấu, fixture và dữ liệu Gather Phase 2. [PR #9](https://github.com/lam2121/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/pull/9) |
| `sim/quan` và contract | Nguyễn Văn Lâm | Cấu hình Quán, món mới, `day_plan`, giữ chỗ, đóng ca và 12 ca Quán. [PR #8](https://github.com/lam2121/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/pull/8) |
| `client/ui` | Nguyễn Duy Hưng | Giao diện 5 ngày, HUD, Shop, pause overlay, tổng kết và adapter snapshot mẫu. [PR #10](https://github.com/lam2121/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/pull/10) |
| `qa` | Đặng Nguyễn Nhật Minh | Smoke kho và ca biên Shop, pause, ngất vì Cá Sấu. [PR #7](https://github.com/lam2121/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/pull/7) |

## Điều kiện chốt bàn giao

Nối runner cho `day` và Shop, xử lý pause ở tầng input/runner, cập nhật bộ mã nguyên liệu tại ranh giới `gather.hold`, rồi chạy lại ba ca đỏ. Khi live có campaign, đối chiếu snapshot và cấu hình qua API trước khi dùng kết quả preview làm bằng chứng UI tích hợp. Đối chiếu các quyết định dữ liệu trong [clarify](../clarify.md) và [retro](../retro.md#phase-2).
