# Ma trận truy vết Phase 3

| AC | Nội dung | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-3/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) | Người |
|---|---|---|---|---|---|
| AC-P3-01 | v1.2: file kho đếm, sai schema, kind lạ, id trùng, fresh ngoài miền → mã 2 | test đơn vị + headless | 7 unit tests trong `tests/test_p3_inventory.py` | đạt | invzble-z |
| AC-P3-02 | Hàng mới fresh=100, hao 0.5/s ở giỏ, 0.25/s ở kho, kẹp 0, pause dừng hao, món chín không hao | test | — | chưa đạt (chờ gộp) | Dũng, Quốc |
| AC-P3-03 | spoiled đúng 1 lần khi từ ≥ 30 xuống < 30, theo id, đúng location | scenario mẫu ticket | — | chưa đạt (chờ gộp) | Dũng, Quốc |
| AC-P3-04 | Giữ theo id tươi nhất. Hàng giữ vừa ươn → nhả, giữ lại 1 lần, thiếu → unfulfillable | test | — | chưa đạt (chờ gộp) | Quoosc |
| AC-P3-05 | `base_price` theo trung bình fresh, boa trên giá đã chốt, `cook_started.items` đúng thứ tự kind -> id. Món chín không hao tươi | 4 unit tests trong `tests/test_p3_quan_price.py` | [`quan-price-test.txt`](docs/proof/phase-3/quan-price-test.txt) | đạt | ttkien0710 |
| AC-P3-06 | lost trong faint/monster_hit là mảng cá thể LIFO | test | — | chưa đạt | comtrang378-ship-it |
| AC-P3-07 | Bàn giao file giữ đúng id/kind/fresh (smoke ticket) | smoke 2 tiến trình | — | chưa đạt | WorkOfMinh |
| AC-P3-08 | Bàn giao trong day cùng tick, id tăng xuyên Ngày | smoke day --days 2 | — | chưa đạt | invzble-z |
| AC-P3-09 | HUD cho thấy độ tươi hoặc hàng ươn | ảnh chụp live | — | chưa đạt | nganhduong123 |
| AC-P3-10 | Regression P1–P2 còn hiệu lực đạt, test đổi có lý do. CHANGELOG có breaking change | chạy toàn bộ test (100/100 tests pass) | [`quan-price-test.txt`](docs/proof/phase-3/quan-price-test.txt) | đạt (100/100 test xanh) | WorkOfMinh, ttkien0710 |

## Đánh giá ngắn
- **Yêu cầu AC-P3-05 (ttkien0710 phụ trách):**
  - Đã cài đặt cơ chế tiêu thụ nguyên liệu theo mảng cá thể `{id, kind, fresh}` hoặc id reserved `["I1", "I2"]`.
  - Tính `base_price = floor(menu_price * avg_fresh / 100)` sử dụng `Fraction`, đảm bảo tính tất định byte-by-byte không sai số float.
  - Tính tiền boa `tip = floor(base_price * 0.2)` trên giá đã chốt khi kiên nhẫn $\ge 50\%$.
  - Mảng `cook_started.items` được sắp xếp theo đúng quy ước: `kind` tăng dần rồi `id` tăng dần.
  - Món đã chín trên bếp không bị hao thêm độ tươi theo thời gian.
  - Giữ tương thích ngược hoàn hảo với kho đếm v1.0/v1.1 (100/100 test của toàn bộ repo chạy xanh).
