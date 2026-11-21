# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

> Quy trình: thành viên gửi câu hỏi cho PO (TV6) → PO hỏi Anh Năm trên lab board (mỗi lần một ý) → ghi câu trả lời. Chưa hỏi được thì ghi **giả định** (đánh dấu `GIẢ ĐỊNH`) theo starter/contract và cập nhật khi có trả lời.
> Trạng thái: `ĐÃ TRẢ LỜI` · `GIẢ ĐỊNH` (chưa xác nhận) · `CHỜ HỎI`.

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | P1 | Hết giờ (180 s) mà chưa về bến thì giữ giỏ hay mất? | `GIẢ ĐỊNH`: giữ giỏ, ghi kho với `gather_end` reason `time` (starter `_finish("time")` xuất kho). | PO, theo starter |
| 2 | P1 | Ngất (Máu 0) thì kho ghi gì? | `GIẢ ĐỊNH`: kho rỗng `{"items":{}}`, reason `fainted` (TODO trong `gather.py`). | PO, theo starter |
| 3 | P1 | Oxy tính theo vị trí đầu hay cuối bước? "Dưới nước" là `d > surface_depth` hay `≥`? | `GIẢ ĐỊNH`: theo `d` **cuối** bước; dưới nước khi `d > 0.5`, mặt nước khi `d ≤ 0.5` (`_at_surface`). | PO, theo starter |
| 4 | P1 | Ngạt: mất Máu đầu tiên sau đúng 60 tick ở oxy 0, rồi cứ 60 tick một lần? Lên mặt nước có reset bộ đếm? | `CHỜ HỎI` (giả định tạm: đủ `choke_interval_ticks` thì −1 Máu và đếm lại; lên mặt nước reset về 0). | — |
| 5 | P1 | Giỏ LIFO: khi đầy thì bắt cá linh (yield 3) mà chỉ còn 1 chỗ thì nhặt 1 hay không nhặt? | `CHỜ HỎI` — ảnh hưởng `fish_caught` / `hold_full`. | — |
| 6 | P1 | Bắt cá xong đàn cá biến mất hay vẫn còn (bắt lại sau hồi chiêu)? | `CHỜ HỎI`. | — |
| 7 | P1 | Hai nút/cá cùng khoảng cách thì chọn cái nào? | `GIẢ ĐỊNH`: id nhỏ hơn (TODO trong `gather.py`). | PO, theo starter |
| 8 | P1 | Khách chọn món thế nào khi kho nấu được nhiều món? Có dùng `Streams` không? | `CHỜ HỎI` — cần PRD-0 mục F. | — |
| 9 | P1 | Khách đến lúc bàn đang có người thì sao (bỏ qua / xếp hàng / `no_dish`)? | `CHỜ HỎI`. | — |
| 10 | P1 | Boa: 20% giá món, làm tròn thế nào? Kiên nhẫn ≥ 50% tính tại lúc phục vụ? | `CHỜ HỎI` (giả định tạm: tại lúc `served`). | — |
| 11 | P1 | Nộp link repo ở đâu, hạn theo múi giờ nào, video demo nộp ở đâu? | `CHỜ HỎI` giảng viên. | — |
| 12 | P1 (Spec Kit) | (bổ sung #4) Ngạt chỉ đếm khi oxy 0 **và** dưới nước? | `GIẢ ĐỊNH`: đúng; đủ `choke_interval_ticks` → −1 Máu, `choke`, đếm lại 0; mặt nước reset 0 (khớp kiểm `zero_oxy_ticks ∈ [0,59]` trong `scenario.py`). | Spec Kit, chờ PO |
| 13 | P1 (Spec Kit) | (bổ sung #5) Giỏ thiếu chỗ cho cả lượt nhặt? | `GIẢ ĐỊNH`: không nhặt gì, phát `hold_full`, không đặt hồi chiêu, nút không mọc lại. | Spec Kit, chờ PO |
| 14 | P1 (Spec Kit) | (bổ sung #6) Đàn cá sau khi bắt? | `GIẢ ĐỊNH`: vẫn còn (cá đứng yên, không có cơ chế sinh lại); hồi chiêu `catch_cooldown_s` chặn bắt liên tục. | Spec Kit, chờ PO |
| 15 | P1 (Spec Kit) | (bổ sung #8) Khách chọn món? | `GIẢ ĐỊNH`: ngẫu nhiên đều qua `Streams.get("quan_order")` trên các món nấu được từ (kho − giữ chỗ), danh sách sắp theo id; giữ chỗ ngay khi khách ngồi. | Spec Kit, chờ PO |
| 16 | P1 (Spec Kit) | (bổ sung #9) Tới lượt khách mà hết bàn? | `GIẢ ĐỊNH`: bỏ lượt, không phát sự kiện; lịch tiếp tục. Có bàn nhưng không món → `no_dish`. | Spec Kit, chờ PO |
| 17 | P1 (Spec Kit) | (bổ sung #10) Boa làm tròn? | `GIẢ ĐỊNH`: `round(price·tip_rate)` (menu hiện tại ra số nguyên); tỉ lệ kiên nhẫn tính lúc `served`; boa kèm uy tín +`tip_reputation`, kẹp [0,5]. | Spec Kit, chờ PO |
| 18 | P1 (Spec Kit) | Bếp nấu món cho khách nào? Kiên nhẫn có giảm khi món đang nấu? | `GIẢ ĐỊNH`: khách chờ id nhỏ nhất mà món chưa nấu/chưa cầm; kiên nhẫn giảm tới lúc `served`. | Spec Kit, chờ PO |
| 19 | P1 (Spec Kit) | Khách bỏ đi khi món đã nấu/đang cầm? | `GIẢ ĐỊNH`: nguyên liệu đã trừ không hoàn; món vẫn còn, phục vụ được khách sau gọi cùng món. Giữ chỗ chưa nấu thì nhả. | Spec Kit, chờ PO |
| 20 | P1 (Spec Kit) | Thứ tự một bước quan (PRD-0 mục F)? | `GIẢ ĐỊNH`: (1) đồng hồ, kiên nhẫn, nấu, ăn theo id → (2) đi lại → (3) một interact → (4) khách mới → (5) hết giờ. Cần PO đối chiếu PRD. | Spec Kit, chờ PO |
| 21 | P1 (Spec Kit) | `customer_arrived` ở tick nào: dòng event `tick == first_customer_tick + k·customer_interval_s·60`? (khác Q-E: đây là lệch k/k+1) | `GIẢ ĐỊNH`: đúng, tính theo tick của dòng event (sau khi tăng tick). | Spec Kit, chờ PO |
| 23 | P1 (research Q-A) | Tick oxy vừa chạm 0 có tính là tick ngạt đầu tiên không? | `GIẢ ĐỊNH`: có (spec FR-004). | PO, chờ PRD-0 |
| 24 | P1 (research Q-B) | Bấm `catch` hụt / gặp `hold_full` có bắt đầu hồi chiêu không? | `GIẢ ĐỊNH`: không, chỉ hồi chiêu khi bắt được. | PO, chờ PRD-0 |
| 25 | P1 (research Q-C) | Cập bến có phải ở mặt nước không? | `GIẢ ĐỊNH`: giữ hành vi khung — chỉ xét bán kính, dưới nước vẫn cập được. `CHỜ HỎI` Anh Năm. | PO |
| 26 | P1 (research Q-D) | Tên + `data` của mọi sự kiện gather/quan (PRD-0 mục E)? | `CHỜ HỎI`; tạm theo `specs/001-phase-1-core/contracts/events.md` (tên trường khớp HUD). Rủi ro lớn nhất cho test ẩn. | PO hỏi, TV1 chốt `docs/contracts/` |
| 27 | P1 (research Q-E) | Lịch khách tính theo tick nào khi scenario đặt `time_left_ticks`? | `GIẢ ĐỊNH`: theo `self.tick` đếm từ đầu lượt chạy. | PO, chờ PRD-0 |
| 28 | P1 (research Q-F) | TV3 có được sửa `chonoi/scenario.py` (file khung) để kiểm mâu thuẫn scenario? | Quyết: không sửa khung; kiểm trong `QuanSim.__init__` (an toàn — `runner.py:78` dựng Session trước khi mở file `--out` ở dòng 80, đã chạy thử: thoát mã 2, không tạo file). | PO + Integrator |
