# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 09:45 | Tên luồng RNG khi chọn món ngẫu nhiên cho khách ở Quán? | Dùng `self.rng.get("customer")`. Sắp xếp các món nấu được theo bảng chữ cái Unicode (key món) trước khi lấy `choice`. | PO & Nhóm thống nhất |
| 2 | 2026-11-21 09:48 | Bắt cá khi giỏ không đủ chỗ (`hold_full`) có kích hoạt hồi chiêu không? | Không phạt hồi chiêu mới (`catch_cd_ticks` giữ nguyên giá trị hiện tại, không đặt lại thành 0.5s). | PO & Nhóm thống nhất |
| 3 | 2026-11-21 09:50 | Tay đang cầm món (`hand != None`) có được bật bếp `idle` để nấu tiếp không? | Có. Bếp `idle` tự động lấy đơn hàng `reserved` cũ nhất để nấu. Chỉ khi nhặt món từ bếp `ready` mới bắt buộc tay phải rỗng (`hand == None`). | PO & Nhóm thống nhất |
| 4 | 2026-11-21 09:52 | Thứ tự các sự kiện khi hết giờ ca làm việc (`time_left_ticks == 0`) ở Quán? | Nếu vừa giao món: `served` -> `paid` (trả tiền ngay) -> `customer_left` (khách chờ rời đi với reason `closing`) -> `quan_end`. | PO & Nhóm thống nhất |
| 5 | 2026-11-21 09:55 | Chạy test trên môi trường Windows với lệnh `python3` trong `game.contract.json`? | Giữ nguyên `"headless_cmd": "python3 -m chonoi.headless"` trong contract cho hệ thống chấm bài Linux; `tests/helpers.py` tự fallback sang `sys.executable` khi chạy trên Windows. | Integrator (Vũ Thành) |
| 6 | 2026-11-21 10:00 | Thứ tự ưu tiên khi có nhiều đối tượng (bếp, bàn) trong bán kính tương tác? | Ưu tiên đối tượng khoảng cách gần nhất -> bếp trước bàn -> ID nhỏ hơn. Nếu đối tượng được chọn không tương tác được thì bỏ lượt (không xét đối tượng kế tiếp). | PO (Đỗ Việt Anh) |
| 7 | 2026-11-21 10:05 | Cơ chế chọn món ngẫu nhiên cho khách mới khi vào quán? | Chỉ chọn trong các món mà tồn khả dụng (tồn vật lý trừ phần giữ chỗ) đủ nấu. Sắp xếp món theo Unicode và chọn đều qua luồng RNG `customer`. Nếu không món nào đủ thì phát `no_dish` và khách không vào bàn. | PO (Đỗ Việt Anh) |
| 8 | 2026-11-21 10:10 | Xử lý trạng thái khi khách hết kiên nhẫn hoặc khi hết ca tối? | Hết kiên nhẫn: trừ 0.5 uy tín, giải phóng giữ chỗ, hủy món trên bếp/tay nếu có (nguyên liệu đã nấu không hoàn lại). Hết ca: khách đang ăn trả tiền ngay, khách đang chờ rời quán với lý do closing và không bị trừ uy tín. | PO (Đỗ Việt Anh) |
