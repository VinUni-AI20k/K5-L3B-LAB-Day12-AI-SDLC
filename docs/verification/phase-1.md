# Ma trận truy vết Phase 1

Kiểm chứng sơ bộ dựa trên PRD-0 và Test Contract v1.0. Cột đầu dẫn đến mục tương ứng của đề. Kết quả dưới đây dùng mã luật trên `main` tại `c872ef2` và test QA `c686e7e`.

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| B–E · CLI, snapshot, đầu vào sai, đầu ra tất định | Smoke test và chạy hai lần luồng cập bến → nạp kho, so JSONL của hai pha và file kho từng byte | [Kết quả trên mã main](../proof/phase-1/qa-headless.md#kết-quả-trên-mã-main) | Đạt trong các ca đã chạy. |
| E–F · Bơi, mép bản đồ, oxy, ngạt và ngất | Chạy smoke chuyển động và test oxy. So dữ liệu `oxygen_empty`, `faint` với mục E | [Kết quả trên mã main](../proof/phase-1/qa-headless.md#kết-quả-trên-mã-main) | Chưa đạt đầy đủ. Chuyển động, nhịp oxy/ngạt và kho rỗng khi ngất đạt. Dữ liệu hai sự kiện còn lệch. |
| F–G · Hái nút vừa mọc lại hoặc bắt cá ở bước cuối | Fixture khởi tạo giỏ rỗng. So thứ tự sự kiện rồi đối chiếu file kho và snapshot quán | [Kết quả trên mã main](../proof/phase-1/qa-headless.md#kết-quả-trên-mã-main) · [Nhánh lát 2](../proof/phase-1/qa-headless.md#kiểm-tra-các-nhánh-đang-phát-triển) | Chưa đạt trên main. Lát 2 chưa được gộp. |
| E–F · Giỏ thiếu chỗ bắt cả đàn | Đặt đàn ưu tiên cần 3 ô, còn 1 ô và có đàn nhỏ hơn cùng vị trí. Kiểm giỏ, danh sách cá, hồi chiêu và `hold_full` | [Nhánh lát 2](../proof/phase-1/qa-headless.md#kiểm-tra-các-nhánh-đang-phát-triển) | Chưa đạt. Nhánh lát 2 giữ được trạng thái đúng, dữ liệu sự kiện còn lệch. |
| F–G · Cập bến, hết giờ, ngất, giới hạn bước và bàn giao kho | Smoke kho dựng sẵn, cập bến đúng bước cuối, nạp kho rỗng sau ngất và giữ nguyên file có sẵn khi chạm giới hạn bước | [Kết quả trên mã main](../proof/phase-1/qa-headless.md#kết-quả-trên-mã-main) | Đạt phần bàn giao file kho trong các ca đã chạy. |
| E–F · Lịch khách, giữ nguyên liệu và `no_dish` | Chạy đến tick khách đầu tiên với kho vừa đủ một món và với kho rỗng | [Kết quả trên mã main](../proof/phase-1/qa-headless.md#kết-quả-trên-mã-main) | Chưa đạt. Thiếu `customer_arrived` và `no_dish`. |
| E–F · Phục vụ đúng tick hết kiên nhẫn và hết ca | Đặt Út Sen cạnh bàn, đã cầm đúng món, còn một tick. Kiểm chuỗi `served` → `paid` → `quan_end` và tiền, uy tín | [Kết quả trên mã main](../proof/phase-1/qa-headless.md#kết-quả-trên-mã-main) · [Nhánh lát 4](../proof/phase-1/qa-headless.md#kiểm-tra-các-nhánh-đang-phát-triển) | Chưa đạt. Main chỉ có `quan_end`. |
| Phạm vi lõi và DoD · HUD và luồng chơi hai buổi | Test HTTP trạng thái, input và HTML. Chơi thử đầy đủ sau khi các lát được gộp | [Kết quả trên mã main](../proof/phase-1/qa-headless.md#kết-quả-trên-mã-main) | Test HTTP đạt. Chưa kiểm chứng thủ công toàn bộ HUD và luồng chơi. |

## Đánh giá ngắn

- Chủ lát 1 đối chiếu `oxygen_empty` và `faint` với mục E. Chủ lát 2 phối hợp xử lý dữ liệu của `gather`, `fish_caught` và `hold_full`.
- Chủ lát 3 và 4 thống nhất schema khách và món theo mục D. Kiểm lại lịch khách và thứ tự xử lý lúc hết kiên nhẫn hoặc đóng ca.
- Khi các lát đã gộp, chạy lại bộ test trên commit bàn giao và cập nhật bằng chứng thực tế trước khi gắn tag.
