# Ma trận truy vết Phase 2

Phạm vi ghi ở đây: phần **QA + UI** (huydn8816). Các AC về luật mô phỏng do các lát khác viết; kết quả ghi theo trạng thái thật
của commit đang chạy. Mã AC do nhóm tự đặt (Phase2.md chỉ gợi ý dạng `AC-P2-xx`).

**Trạng thái commit được kiểm:** nhánh `huydn8816` đã gộp `main` (`e08683e`); `game.contract.json` còn `contract_version: "1.0"`;
chưa có chế độ `--mode day`, pause, Cá Sấu, Shop trong code. Các test Phase 2 tự bỏ qua khi contract chưa là `1.1`.
Cách bật: đổi `contract_version` sang `"1.1"` rồi chạy `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`.

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P2-01 Số chuẩn gather (8 đàn, N1–N6, yield 3 loài, khóa cá bơi/sinh) | `tests/test_p2_contract.py::Gather` | `docs/proof/phase-2/regression-p1.txt` (46 test bỏ qua vì contract 1.0) | **Chưa kiểm** — contract chưa chuyển 1.1 |
| AC-P2-02 Số chuẩn Cá Sấu (M1/M2, bất tử 90, loss_ratio 0.5) | `test_p2_contract.py::Monster` | như trên | **Chưa kiểm** — như trên |
| AC-P2-03 Số chuẩn quán (B1–B2, T1–T4, 6 món) | `test_p2_contract.py::Quan` | như trên | **Chưa kiểm** — như trên |
| AC-P2-04 day_plan D1–D5 và Shop | `test_p2_contract.py::DayShop` (kiểm cả tổng công thức × số suất) | như trên | **Chưa kiểm** — như trên |
| AC-P2-05 Cá bơi/sinh | `test_p2_rules.py::Ca` | — | **Chưa kiểm** — luật chưa có trong code |
| AC-P2-06 Cá Sấu: tuần tra, chase, hit, ngất | `test_p2_rules.py::Sau` | — | **Chưa kiểm** — luật chưa có |
| AC-P2-07 Quán 4 bàn, lẩu mắm, lượt khách 120 + 900k | `test_p2_rules.py::Quan` | — | **Chưa kiểm** — số chuẩn chưa áp dụng |
| AC-P2-08 `--mode day`: kế hoạch ngày, đổi pha cùng tick, `--days` | `test_p2_rules.py::Day` | — | **Chưa kiểm** — chưa có mode day |
| AC-P2-09 Shop: buy, shop_done, nâng cấp hiệu lực Ngày sau | `test_p2_rules.py::Shop` | — | **Chưa kiểm** — chưa có Shop |
| AC-P2-10 Pause/resume | `test_p2_rules.py::Pause` | — | **Chưa kiểm** — chưa có pause |
| AC-P2-11 Hiệu năng một Ngày ≤ 20 s | `test_p2_rules.py::Hieunang` | — | **Chưa kiểm** — chưa có mode day |
| AC-P2-12 Smoke tích hợp `gather --inventory-out` → `quan --inventory` | Chơi thật `gather` (hái N1, cập bến) rồi mở `quan` với file kho; so snapshot tick 0 | `docs/proof/phase-2/integration.*` (inputs, gather.jsonl, inventory.json, quan.jsonl) | **Đạt** (số chuẩn v1.0). Kho `{"bong_dien_dien":1}`; quan tick 0 `stock` khớp; `docked` ở tick 261 |
| AC-P2-13 Tất định (cùng seed → cùng từng byte) | Chạy lại lệnh gather của AC-P2-12, `cmp` JSONL và file kho | lệnh ghi trong `integration.md` | **Đạt** |
| AC-P2-14 Regression Phase 1 | Bộ test đầy đủ trên commit đang kiểm | `docs/proof/phase-2/regression-p1.txt`: 135 test, OK, 46 bỏ qua | **Đạt với số v1.0**; **chưa kiểm với số chuẩn v1.1** (contract chưa đổi) |
| AC-P2-15 UI: menu, tạm dừng, HUD sáng/tối, chữ ≥ 18 px | Chụp Chrome 1280×720 | `ui-menu.png`, `ui-gather-that.png`, `ui-quan-that.png` (máy chủ thật); `ui-*-snapshot-gia.png` (snapshot soạn tay) | **Đạt một phần**: hiển thị đúng với dữ liệu hiện có. Chưa kiểm với backend `day`/pause thật; chưa đo FPS |
| AC-P2-16 UI: Shop, DayIntro/EveningIntro, DayResult, Tổng kết | Như trên, bằng snapshot giả | `ui-shop-*`, `ui-dayintro-*`, `ui-pause-*` | **Đạt một phần**: chỉ dựng hình từ snapshot giả; lệnh `pause`/`buy`/`shop_done` chưa có backend nhận |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt: đạt smoke tích hợp, tất định, regression Phase 1 (số v1.0) và hiển thị UI với dữ liệu hiện có. Chưa đạt
  (chưa kiểm được): mọi luật và số chuẩn riêng của Phase 2 vì code mới ở mức Phase 1 + các lát gather trên `main`.
- Điều cần chỉnh cho phase sau: Integrator đổi `contract_version` sang `1.1` khi tích hợp xong để 46 test Phase 2 chạy; người làm
  `day` cần nhận các nút `pause`, `shop_done`, chuỗi `buy` ở `/input` để UI dùng được; chạy lại bảng này sau khi bật test.
- Giới hạn của bằng chứng: ảnh `*-snapshot-gia.png` dựng từ snapshot soạn tay, không phải từ mô phỏng thật.
