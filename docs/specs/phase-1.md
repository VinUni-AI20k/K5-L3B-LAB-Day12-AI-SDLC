# Spec — Phase 1: Quán Ăn Chợ Nổi (contract v1.0)

> Nguồn: PRD-0 Phase 1 (lab board `#phase-1`) + Test Contract v1.0. Đặc tả từng khóa: `docs/plan/phase-1-conformance.md`.
> Spec này nói **cái gì** và **vì sao**; conformance nói **chính xác từng con số/payload**.

## Problem Statement

Người chơi vào vai Út Sen, cô bé ở chợ nổi Rạch Sen. Ban ngày em phải lặn xuống sông Chín Khúc bắt cá và hái rau trước khi hết oxy; ban đêm em nấu và phục vụ khách trên nhà bè của Má Tư trước khi khách bỏ đi vì chờ lâu. Hiện repo chỉ có khung: bơi được, cập bến được, nhưng **không có oxy, không có hái, không có cá, không có khách, không có nấu** — chơi không ra game và không có gì để chấm.

## Solution

Hoàn thiện trọn một ngày của Út Sen trong đúng contract v1.0: buổi sáng lặn/hái/bắt/cập bến, bàn giao giỏ qua file kho; buổi tối nhận khách, nấu, bưng, phục vụ, thu tiền và giữ uy tín. Hai buổi chạy độc lập bằng hai tiến trình headless nối nhau qua file kho, cùng một lớp luật với cửa sổ chơi trực tiếp.

## User Stories

1. Là người chơi, tôi muốn thấy thanh oxy giảm khi lặn sâu, để biết khi nào phải nổi lên.
2. Là người chơi, tôi muốn bị mất Máu khi ngạt quá lâu, để có áp lực thời gian thật.
3. Là người chơi, tôi muốn ngất thì mất cả giỏ, để mỗi chuyến lặn là một canh bạc.
4. Là người chơi, tôi muốn hái bông súng/bông điên điển ở mặt nước, để có nguyên liệu nấu.
5. Là người chơi, tôi muốn nút hái mọc lại sau một lúc, để không hái một chỗ mãi.
6. Là người chơi, tôi muốn bắt đàn cá bằng phím Space khi đang lặn, để có cá cho món chính.
7. Là người chơi, tôi muốn cá linh cho nhiều hơn cá lóc, để biết nên đuổi đàn nào.
8. Là người chơi, tôi muốn giỏ có giới hạn, để phải chọn mang gì về.
9. Là người chơi, tôi muốn cập bến là kết thúc buổi sáng và giữ những gì đã hái, để chủ động về sớm.
10. Là người chơi, tôi muốn buổi sáng tự kết thúc khi hết giờ, để không bị treo.
11. Là khách, tôi muốn được giữ chỗ nguyên liệu ngay khi gọi món, để món tôi gọi không bị người khác dùng mất.
12. Là người chơi, tôi muốn biết khách còn kiên nhẫn bao lâu, để ưu tiên đúng người.
13. Là người chơi, tôi muốn nấu ở bếp và bưng món đúng đơn, để không bị bỏ lượt vì sai món.
14. Là người chơi, tôi muốn khách ăn xong trả tiền và có thể boa, để nỗ lực được đền.
15. Là người chơi, tôi muốn khách bỏ đi thì mất uy tín, để phục vụ chậm có giá của nó.
16. Là người chơi, tôi muốn hết ca thì khách còn ăn vẫn trả tiền, để không bị mất công vô lý.
17. Là người chơi, tôi muốn HUD hiện thời gian, oxy, Máu, giỏ, kho, món gọi, kiên nhẫn, bếp, tay, tiền, uy tín, để chơi mà không phải đoán.
18. Là người chấm, tôi muốn chạy hai lệnh headless liên tiếp và thấy quán nhận đúng kho, để kiểm tích hợp tự động.
19. Là người chấm, tôi muốn cùng seed cho ra JSONL giống từng byte, để kết quả tái lập được.
20. Là người chấm, tôi muốn fixture dựng được mọi nhánh (khách đang ăn, bếp đang nấu, giỏ đầy, sắp ngạt), để test biên không cần chơi thật.

## Implementation Decisions

- **Bốn lát song song** đúng PRD §6.2; mỗi lát là một đường dọc: luật → snapshot → event → test.
- **Tách helper**: luật gather chia `sim/gather` (điều phối bước, oxy, ngất) và `sim/gather_actions` (hái, bắt, chọn mục tiêu); luật quán chia `sim/quan_customers` (khách, giữ chỗ, kiên nhẫn) và `sim/quan_service` (bếp, bưng, phục vụ, tiền). Quy ước: chỉ một người sửa `step()` của mỗi sim.
- **Thứ tự một bước là hợp đồng**, không phải chi tiết cài đặt: giờ → mọc lại → bơi → dive/surface → oxy theo độ sâu cuối bước → ngạt/ngất → interact (bến trước, hái sau) → catch → hết giờ. Quán: giờ → timer → bếp → đi → **tối đa một** interact → ăn/trả tiền → khách bỏ đi → đóng ca → sinh khách.
- **Event và payload cố định** theo PRD §E (18 event, xem `docs/contracts/README.md`). Không đổi tên, không đổi khóa, không đổi thứ tự event trong một bước.
- **Snapshot chỉ thêm, không đổi tên/xóa**. `quan.tables[]` thêm `customer_id`; chỉ liệt kê khách còn ngồi.
- **Fixture là hợp đồng thứ hai**: scenario phải dựng được trạng thái giữa chừng (khách `reserved/assigned/unfulfillable/served`, bếp `cooking/ready`, tay đang giữ món, giỏ đầy) và từ chối dữ liệu mâu thuẫn bằng mã 2.
- **Số liệu chỉ đọc từ `game.contract.json`**; ngẫu nhiên chỉ qua `Streams`; không dùng đồng hồ thực trong luật.
- **UI chỉ đọc snapshot**, mọi hiệu ứng nằm ngoài `chonoi/`; headless không bị ảnh hưởng.
- **Chọn đối tượng tương tác**: khoảng cách → bếp trước bàn → id; đối tượng đã chọn mà không tương tác được thì **bỏ lượt**, không thử đối tượng khác.

## Testing Decisions

- Test **hộp đen qua `headless_cmd`** là chuẩn vàng: dựng scenario + inputs, đọc JSONL/file kho, so sánh. Không import module nội bộ để test luật.
- Test chỉ khẳng định **hành vi quan sát được**: vị trí, bộ đếm, event + payload, snapshot, file kho, mã thoát. Không khẳng định cấu trúc nội bộ.
- Dung sai đúng PRD: toạ độ ±0.1 m, uy tín ±0.01, thời gian ±2 tick; còn tiền, điểm, id, số lượng, countdown, lý do, thứ tự event, tick biên thì **so chính xác**.
- Mỗi lát có test riêng; QA giữ bộ chạy 1 lệnh + ma trận AC → bằng chứng → đạt/chưa đạt.
- Có test tích hợp hai tiến trình `gather → file kho → quan` và test tất định (cùng seed → cùng byte).
- Ưu tiên test biên đúng chỗ hidden test hay chấm: choke ở `t+59`, bắt cá xóa đàn, hồi chiêu 30 tick, boa đúng ngưỡng kiên nhẫn, đóng ca.

## Out of Scope

- Mục **"Mở rộng"** của PRD và Phase 2–4 (chưa có nội dung trên board).
- Đổi công nghệ, engine, asset ngoài; mạng nhiều người; lưu điểm; âm thanh có sẵn file.
- Thay đổi `tests/test_smoke_p1.py`, schema kho, tên event, CLI, mã thoát.
- Cân bằng số liệu (dùng nguyên preset).

## Further Notes

- Bản sao PRD-0 công khai: `NgChiVinh/K5-L3B-LAB-Day12-AI-SDLC-nhom6ae/docs/prd/phase-1.md` — **thiếu** danh sách mục mở rộng; cần lấy từ board hoặc hỏi Anh Năm.
- 8 câu hỏi mơ hồ đang chờ Anh Năm: `docs/clarify.md`.
- Định nghĩa hoàn thành của phase: PRD §7 (chơi được hai buổi, HUD đọc được, contract khớp, smoke hai tiến trình, README 3 lệnh, TEAM/team_size, hợp đồng kho, verification + bằng chứng, tag `phase-1`).
