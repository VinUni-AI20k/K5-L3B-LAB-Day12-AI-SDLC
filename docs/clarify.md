# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

> Quy trình: thành viên gửi câu hỏi cho PO (TV6) → PO hỏi Anh Năm trên lab board (mỗi lần một ý) → ghi câu trả lời. Chưa hỏi được thì ghi **giả định** (đánh dấu `GIẢ ĐỊNH`) theo starter/contract và cập nhật khi có trả lời.
> Trạng thái: `ĐÃ TRẢ LỜI` · `GIẢ ĐỊNH` (chưa xác nhận) · `CHỜ HỎI`.

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | P1 | Hết giờ (180 s) mà chưa về bến thì giữ giỏ hay mất? | `ĐÃ TRẢ LỜI (TICKET-02 §1.1)`: `time` khi hết giờ ở bất kỳ độ sâu, giữ phần còn trong giỏ. | TICKET-02 |
| 2 | P1 | Ngất (Máu 0) thì kho ghi gì? | `ĐÃ TRẢ LỜI (TICKET-02 §1.1)`: `fainted` khi Máu 0, mất toàn bộ giỏ; trong `day` vẫn mở quán với kho rỗng. | TICKET-02 |
| 3 | P1 | Oxy tính theo vị trí đầu hay cuối bước? "Dưới nước" là `d > surface_depth` hay `≥`? | `GIẢ ĐỊNH`: theo `d` **cuối** bước; dưới nước khi `d > 0.5`, mặt nước khi `d ≤ 0.5` (`_at_surface`). | PO, theo starter |
| 4 | P1 | Ngạt: mất Máu đầu tiên sau đúng 60 tick ở oxy 0, rồi cứ 60 tick một lần? Lên mặt nước có reset bộ đếm? | `ĐÃ TRẢ LỜI (TICKET-02 §1.1)`: dưới nước oxy 0 → −1 Máu mỗi 60 tick, **tính cả bước vừa chạm 0**; reset nhịp khi **oxy > 0 hoặc lên mặt nước**. Ngạt xuyên bất tử, không rơi hàng. | TICKET-02 |
| 5 | P1 | Giỏ LIFO: khi đầy thì bắt cá linh (yield 3) mà chỉ còn 1 chỗ thì nhặt 1 hay không nhặt? | `ĐÃ TRẢ LỜI (TICKET-02 §1.1)`: cần đủ chỗ cho **cả đàn**, thiếu thì không bắt (`hold_full`). | TICKET-02 |
| 6 | P1 | Bắt cá xong đàn cá biến mất hay vẫn còn (bắt lại sau hồi chiêu)? | `CHỜ HỎI`. | — |
| 7 | P1 | Hai nút/cá cùng khoảng cách thì chọn cái nào? | `ĐÃ TRẢ LỜI`: hòa theo id (cá), quán: bếp trước bàn rồi id. | TICKET-02 |
| 8 | P1 | Khách chọn món thế nào khi kho nấu được nhiều món? Có dùng `Streams` không? | `ĐÃ TRẢ LỜI (TICKET-02 §2)`: chọn đều theo seed trong các món đủ nguyên liệu sau khi trừ phần giữ (mode `day`: chỉ món trong kế hoạch; quán riêng: cả 6 món). | TICKET-02 |
| 9 | P1 | Khách đến lúc bàn đang có người thì sao (bỏ qua / xếp hàng / `no_dish`)? | `ĐÃ TRẢ LỜI (TICKET-02 §1.3)`: khách chỉ đến nếu có bàn trống, ngồi ghế trống id nhỏ nhất; có bàn mà thiếu món → `no_dish`. | TICKET-02 |
| 10 | P1 | Boa: 20% giá món, làm tròn thế nào? Kiên nhẫn ≥ 50% tính tại lúc phục vụ? | `ĐÃ TRẢ LỜI (TICKET-02 §1.3)`: boa `floor(giá × 0.2)` nếu còn ≥ 50% kiên nhẫn **lúc giao**; boa dương → uy tín +0.2. | TICKET-02 |
| 11 | P1 | Nộp link repo ở đâu, hạn theo múi giờ nào, video demo nộp ở đâu? | `CHỜ HỎI` giảng viên. | — |
| 12 | P1 (Spec Kit) | (bổ sung #4) Ngạt chỉ đếm khi oxy 0 **và** dưới nước? | `ĐÃ TRẢ LỜI`: như #4. | TICKET-02 |
| 13 | P1 (Spec Kit) | (bổ sung #5) Giỏ thiếu chỗ cho cả lượt nhặt? | `ĐÃ TRẢ LỜI`: như #5. | TICKET-02 |
| 14 | P1 (Spec Kit) | (bổ sung #6) Đàn cá sau khi bắt? | `ĐÃ TRẢ LỜI một phần (TICKET-02)`: cá bơi 1.5 m/s và sinh thêm theo lịch (trần 12); đàn bị bắt bị loại — `GIẢ ĐỊNH` (đề không nói thẳng). | TICKET-02 |
| 15 | P1 (Spec Kit) | (bổ sung #8) Khách chọn món? | `ĐÃ TRẢ LỜI`: như #8. | TICKET-02 |
| 16 | P1 (Spec Kit) | (bổ sung #9) Tới lượt khách mà hết bàn? | `ĐÃ TRẢ LỜI`: như #9. | TICKET-02 |
| 17 | P1 (Spec Kit) | (bổ sung #10) Boa làm tròn? | `ĐÃ TRẢ LỜI — GIẢ ĐỊNH CŨ SAI`: dùng `floor`, không `round`. | TICKET-02 |
| 18 | P1 (Spec Kit) | Bếp nấu món cho khách nào? Kiên nhẫn có giảm khi món đang nấu? | `ĐÃ TRẢ LỜI — GIẢ ĐỊNH CŨ SAI (TICKET-02 §1.3)`: bếp lấy đơn `reserved` cũ nhất theo `order_tick` rồi id bàn. | TICKET-02 |
| 19 | P1 (Spec Kit) | Khách bỏ đi khi món đã nấu/đang cầm? | `GIẢ ĐỊNH`: nguyên liệu đã trừ không hoàn; món vẫn còn, phục vụ được khách sau gọi cùng món. Giữ chỗ chưa nấu thì nhả. | Spec Kit, chờ PO |
| 20 | P1 (Spec Kit) | Thứ tự một bước quan (PRD-0 mục F)? | `GIẢ ĐỊNH`: (1) đồng hồ, kiên nhẫn, nấu, ăn theo id → (2) đi lại → (3) một interact → (4) khách mới → (5) hết giờ. Cần PO đối chiếu PRD. | Spec Kit, chờ PO |
| 21 | P1 (Spec Kit) | `customer_arrived` ở tick nào: dòng event `tick == first_customer_tick + k·customer_interval_s·60`? (khác Q-E: đây là lệch k/k+1) | `ĐÃ TRẢ LỜI (TICKET-02 §1.3)`: khách tại tick 120 + 900·k (k ≥ 0). | TICKET-02 |
| 23 | P1 (research Q-A) | Tick oxy vừa chạm 0 có tính là tick ngạt đầu tiên không? | `ĐÃ TRẢ LỜI`: có (như #4). | TICKET-02 |
| 24 | P1 (research Q-B) | Bấm `catch` hụt / gặp `hold_full` có bắt đầu hồi chiêu không? | `ĐÃ TRẢ LỜI`: hồi 30 tick tính từ lần bắt **thành công**. | TICKET-02 |
| 25 | P1 (research Q-C) | Cập bến có phải ở mặt nước không? | `ĐÃ TRẢ LỜI`: `docked` khi tương tác trong bán kính bến (không đòi mặt nước); bến xét trước hái và trước bắt cá. | TICKET-02 |
| 26 | P1 (research Q-D) | Tên + `data` của mọi sự kiện gather/quan (PRD-0 mục E)? | `ĐÃ TRẢ LỜI một phần (TICKET-02 §4.4–4.5)`: thứ tự bước gather/đổi pha và `data` các event mới đã có; `data` event v1.0 vẫn theo `specs/001-phase-1-core/contracts/events.md`. | TICKET-02 |
| 27 | P1 (research Q-E) | Lịch khách tính theo tick nào khi scenario đặt `time_left_ticks`? | `ĐÃ TRẢ LỜI`: như #21. | TICKET-02 |
| 28 | P1 (research Q-F) | TV3 có được sửa `chonoi/scenario.py` (file khung) để kiểm mâu thuẫn scenario? | Quyết: không sửa khung; kiểm trong `QuanSim.__init__` (an toàn — `runner.py:78` dựng Session trước khi mở file `--out` ở dòng 80, đã chạy thử: thoát mã 2, không tạo file). | PO + Integrator |
| 29 | 2026-11-21 (TV1, gộp từ main; trước là #1) | PRD-0 mục E không đọc được (lab board yêu cầu đăng nhập, Phase 1 hiện "Chưa phát hành"). `data` của `oxygen_empty`, `choke`, `faint` lấy thế nào? | Giả định: `dive`/`surface` theo comment starter `{"pos":[x,d]}`; `oxygen_empty` và `faint` là `{}`; `choke` là `{"hp": máu còn sau khi trừ}`; `hold_full` là `{"kind": id món bị từ chối}`. Đủ `choke_interval_ticks` tick oxy = 0 dưới nước thì trừ Máu và đưa `zero_oxy_ticks` về 0. — **PO (TICKET-02):** phần ngạt/reset đã chốt ở #4 (reset cả khi oxy > 0). `faint` ở v1.1 thêm `cause` (khi do bị chạm), `hp:0` và phần giỏ còn lại (§4.4); `data` các event còn lại vẫn là giả định của TV1, giữ nguyên. | TV1 + PO |
| 30 | P2 (research P2-Q3) | Ngất do **ngạt** (không phải bị chạm) thì `faint.data` có `lost`/`hp` không? | `CHỜ HỎI`. `GIẢ ĐỊNH`: có `hp:0` và `lost` = phần giỏ còn lại, không có `cause` (đề chỉ nói `cause:"monster"` khi do bị chạm). | PO |
| 31 | P2 (research P2-Q7) | Cá Sấu hit cần người chơi ở đâu? | `ĐÃ TRẢ LỜI (TICKET-02 §1.2)`: sau khi cả hai di chuyển, khoảng cách ≤ 1.5 m, người chơi ở **d ≥ 10** và hết bất tử. | TICKET-02 |
| 32 | P2 (research P2-Q8) | `extensions` ở gốc manifest là mảng mã hay object? | `CHỜ HỎI`. `GIẢ ĐỊNH`: mảng chuỗi mã, vd. `["burn","snake"]`. | PO |
| 33 | P2 (research P2-Q9) | Đàn cá bị bắt có biến mất không? | `CHỜ HỎI`. `GIẢ ĐỊNH`: biến mất (đề có trần 12 đàn và sinh lại theo lịch → ngầm hiểu bị loại). | PO |
