# Ma trận truy vết Phase 1

Kết quả QA sơ bộ trên `origin/main` tại `c3441f9`, đối chiếu PRD-0 và Test Contract v1.0. Chưa có tag `phase-1` tại thời điểm kiểm tra.

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| B–E · CLI, snapshot và tính tất định | Chạy smoke, rồi chạy cùng seed và cùng đầu vào hai lần để so byte JSONL và kho | [Log unittest](../proof/phase-1/unittest.txt) | **Đạt** ở các ca đã chạy. Smoke cũng xác nhận mã 2 ở các ca dữ liệu sai đã có. |
| E–F · Di chuyển, oxy, ngạt và ngất | Chạy smoke di chuyển, test oxy và kiểm tra dữ liệu `oxygen_empty`, `faint` | [Kết quả trên main](../proof/phase-1/qa-headless.md#kết-quả-trên-mã-main) | **Chưa đạt đầy đủ.** Luật di chuyển, oxy, ngạt và kho rỗng khi ngất qua test. Hai sự kiện lệch hợp đồng. |
| E–G · Hái nút vừa mọc lại và bắt cá ở bước cuối | Dựng giỏ rỗng, đối chiếu sự kiện, file kho và kho quán ở tick 0 | [Kết quả QA](../proof/phase-1/qa-headless.md) | **Chưa đạt.** Thiếu hành động trên main. Nhánh lát 2 đã giao được kho nhưng dữ liệu sự kiện còn lệch. |
| E–F · Giỏ thiếu chỗ và hồi chiêu bắt cá | Đặt hai đàn cùng vị trí, đàn ưu tiên cần 3 ô và giỏ còn 1 ô. Kiểm `hold_full`, giỏ, cá và hồi chiêu | [Kết quả nhánh lát 2](../proof/phase-1/qa-headless.md#kiểm-tra-các-nhánh-đang-phát-triển) | **Chưa đạt.** Nhánh lát 2 giữ đúng trạng thái, còn thiếu các trường bắt buộc của `hold_full`. |
| F–G · Cập bến, hết giờ, ngất và giới hạn bước | Kiểm cả ba lý do kết thúc, chuyển kho dựng sẵn sang quán và thử giới hạn bước với file kho có sẵn | [Kết quả trên main](../proof/phase-1/qa-headless.md#kết-quả-trên-mã-main) | **Đạt** phần kết thúc và bàn giao kho trong các ca đã chạy. |
| D–F · Khách đến, chọn món, giữ chỗ và kiên nhẫn | Chạy ở tick khách đầu tiên với kho đủ một công thức và kho rỗng | [Kết quả trên main](../proof/phase-1/qa-headless.md#kết-quả-trên-mã-main) | **Chưa đạt.** Thiếu `customer_arrived` và `no_dish`. Các ca khách hết kiên nhẫn và dọn nguyên liệu còn chờ luật khách. |
| D–F · Nấu, bưng, phục vụ, thu tiền và uy tín | Kiểm phục vụ tại bàn đúng tick hết kiên nhẫn và hết ca. Đối chiếu thứ tự sự kiện, tiền và uy tín | [Kết quả QA](../proof/phase-1/qa-headless.md) | **Chưa đạt.** Main chỉ có `quan_end`. Nhánh lát 4 lỗi ở fixture hợp lệ. Luồng nấu đến thu tiền còn cần chạy trên bản tích hợp. |
| DoD · Hai buổi chơi được và HUD tối thiểu | Chạy test HTTP trạng thái, input và HTML. Chơi thử toàn bộ luồng để đối chiếu HUD | [Log unittest](../proof/phase-1/unittest.txt) | Test HTTP **đạt**. Chưa kiểm chứng thủ công toàn bộ hai buổi và HUD. |
| DoD · Hồ sơ nhóm và bàn giao | Chạy `python tools/check_team.py`, kiểm tra tag, ghi bằng chứng đúng commit | [Danh sách nhóm](../../TEAM.md) · [Bằng chứng QA](../proof/phase-1/qa-headless.md) | Dòng Kaylez đã đủ. Còn bốn dòng thành viên trống họ tên và handle trên nhánh QA. Chưa có tag kiểm chứng. |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt:
  - `origin/main` qua 41/41 test có sẵn. Thêm bộ test tích hợp QA cho kết quả 43/50, với 7 phương thức chưa đạt. Cần chốt lại dữ liệu sự kiện và hoàn thành tích hợp hai buổi trước khi xác nhận DoD.
- Điều cần chỉnh cho phase sau:
  - Đối chiếu tên trường và thứ tự sự kiện với PRD trước khi gộp lát. Chạy lại toàn bộ test trên commit bàn giao và cập nhật log trước khi Lead gắn tag.
