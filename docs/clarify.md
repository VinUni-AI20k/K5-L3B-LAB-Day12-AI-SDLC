# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

> Hướng dẫn: PO (`chur04`) đối chiếu từng câu với **PRD-0** trên Lab Board (hoặc hỏi giảng viên nếu PRD không nêu rõ) rồi điền cột **Trả lời / giả định** và **Ai quyết**.

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | Phase 1 Kickoff | **Gather — Bắt cá khi giỏ gần đầy:** `ca_linh` có `fish_yield = 3`. Nếu giỏ còn 1–2 chỗ trống thì nhận phần còn chỗ rồi phát `hold_full`, hay từ chối cả đàn cá và không xóa cá? | *(chờ đối chiếu PRD-0)* | PO (`chur04`) |
| 2 | Phase 1 Kickoff | **Gather — Cooldown `catch`:** `catch_cd_ticks` (`catch_cooldown_s = 0.5`) kích hoạt mỗi lần bấm `catch` dưới nước (kể cả bắt trượt / đầy giỏ) hay chỉ khi bắt trúng cá? | *(chờ đối chiếu PRD-0)* | PO (`chur04`) |
| 3 | Phase 1 Kickoff | **Gather — Oxy & ngạt:** Khi `oxygen_ticks` vừa giảm từ >0 về 0, `zero_oxy_ticks` bắt đầu tăng ngay trong tick đó hay tick sau? Khi nổi lên mặt nước (`d <= surface_depth`), `zero_oxy_ticks` có reset về 0 ngay không? | *(chờ đối chiếu PRD-0)* | PO (`chur04`) |
| 4 | Phase 1 Kickoff | **Gather — Schema sự kiện:** Danh sách key chính xác trong `data` của các event `dive`, `surface`, `oxygen_empty`, `choke`, `faint`, `gather`, `fish_caught`, `hold_full` là gì? | *(chờ đối chiếu PRD-0)* | PO (`chur04`) |
| 5 | Phase 1 Kickoff | **Quan — Khách chọn món & `no_dish`:** Khách mới đến chọn món nấu được bằng tên RNG stream nào? Nếu không nấu được món nào thì phát `no_dish` và không tạo khách (không trừ uy tín) đúng không? | *(chờ đối chiếu PRD-0)* | PO (`chur04`) |
| 6 | Phase 1 Kickoff | **Quan — `interact` bếp/bàn:** Bấm `interact` ở bếp `idle` chọn nấu món của khách nào (kiên nhẫn thấp nhất / id nhỏ nhất / FIFO)? Đang cầm món (`hand != null`) có bấm nấu bếp khác được không? | *(chờ đối chiếu PRD-0)* | PO (`chur04`) |
| 7 | Phase 1 Kickoff | **Quan — Tiền, tip & uy tín:** Tip (`price * tip_rate` khi tỷ lệ kiên nhẫn ≥ `tip_min_patience_ratio`) làm tròn kiểu nào (`round` / `floor`)? Phục vụ không có tip có cộng uy tín không? | *(chờ đối chiếu PRD-0)* | PO (`chur04`) |
| 8 | Phase 1 Kickoff | **Scenario `quan` (mã thoát 2):** Các trường bắt buộc và điều kiện mâu thuẫn của `customers[]`, `stoves[]`, `hand`, `reserved` trong `scenario.py` theo mục D của PRD-0 là gì? | *(chờ đối chiếu PRD-0)* | PO (`chur04`) |
