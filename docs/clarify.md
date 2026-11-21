# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | Phase 1 | Giỏ còn thiếu chỗ cho cả mẻ (vd. còn 2 chỗ, bắt `ca_linh` được 3) thì thêm một phần hay không thêm gì? | Giả định: không thêm gì, phát `hold_full` | ✅ Ticket P2: "Cần đủ chỗ cho cả đàn" |
| 2 | Phase 1 | Tick đầu tiên oxy chạm 0 có tính là tick ngạt đầu tiên không? | Giả định: có (đếm ngay tick oxy về 0) | ✅ Ticket P2: "tính cả bước vừa chạm 0" |
| 3 | Phase 1 | `data` của dive/surface/oxygen_empty/choke/faint/hold_full gồm những trường nào? | Giả định: xem `docs/contracts/events.md` | ❌ Ticket P2: `faint` có `hp: 0`, `lost` là mảng, `cause` khi do quái → đã sửa |
| 4 | Phase 1 | `invuln_ticks` dùng vào việc gì ở phase 1? | Giả định: chưa dùng, để cho phase sau | ✅ Ticket P2: bất tử 90 tick sau khi Cá Sấu chạm; ngạt xuyên bất tử |
| 5 | Phase 2 | Hướng ban đầu của đàn cá "theo seed" lấy thế nào? | Giả định: góc đều trong [0, 360) từ luồng RNG `fish_spawn` | Lead, chờ PO xác nhận |
| 6 | Phase 2 | Chọn loài và điểm khi sinh dùng chung một luồng RNG? | Giả định: luồng `fish_spawn` cho loài, điểm và hướng (theo thứ tự đó) | Lead, chờ PO xác nhận |
