# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 09:45 | Tên luồng RNG khi chọn món ngẫu nhiên cho khách ở Quán? | Dùng `self.rng.get("customer")`. Sắp xếp các món nấu được theo bảng chữ cái Unicode (key món) trước khi lấy `choice`. | PO & Nhóm thống nhất |
| 2 | 2026-11-21 09:48 | Bắt cá khi giỏ không đủ chỗ (`hold_full`) có kích hoạt hồi chiêu không? | Không phạt hồi chiêu mới (`catch_cd_ticks` giữ nguyên giá trị hiện tại, không đặt lại thành 0.5s). | PO & Nhóm thống nhất |
| 3 | 2026-11-21 09:50 | Tay đang cầm món (`hand != None`) có được bật bếp `idle` để nấu tiếp không? | Có. Bếp `idle` tự động lấy đơn hàng `reserved` cũ nhất để nấu. Chỉ khi nhặt món từ bếp `ready` mới bắt buộc tay phải rỗng (`hand == None`). | PO & Nhóm thống nhất |
| 4 | 2026-11-21 09:52 | Thứ tự các sự kiện khi hết giờ ca làm việc (`time_left_ticks == 0`) ở Quán? | Nếu vừa giao món: `served` -> `paid` (trả tiền ngay) -> `customer_left` (khách chờ rời đi với reason `closing`) -> `quan_end`. | PO & Nhóm thống nhất |
| 5 | 2026-11-21 09:55 | Chạy test trên môi trường Windows với lệnh `python3` trong `game.contract.json`? | Giữ nguyên `"headless_cmd": "python3 -m chonoi.headless"` trong contract cho hệ thống chấm bài Linux; `tests/helpers.py` tự fallback sang `sys.executable` khi chạy trên Windows. | Integrator (Vũ Thành) |
