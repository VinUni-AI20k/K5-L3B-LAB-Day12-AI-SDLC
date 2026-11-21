# 01: Prefactor + fixture contract

**What to build:** Dựng sẵn đường cho bốn lát chạy song song: ba module luật phụ (`gather_actions`, `quan_customers`, `quan_service`) rỗng nhưng đã được `step()` gọi đúng chỗ, snapshot có đủ trường mà PRD §E yêu cầu, và fixture (scenario) dựng được trạng thái giữa chừng của cả hai buổi. Sau ticket này, bốn người có thể code mà không sửa cùng một hàm.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] `--ticks 0` với scenario đầy đủ (khách đang ăn, bếp đang nấu, tay đang giữ món) chạy mã 0; snapshot có `hand`, `stoves[].ready_ticks`, `tables[].customer_id`, `customers[]` chỉ gồm khách còn ngồi.
- [ ] `phase_tick` bắt đầu 0 và tăng 1 mỗi bước; `sim_tick` bằng số bước đã chạy; lịch khách tính theo `phase_tick` sau tăng.
- [ ] Scenario từ chối bằng mã 2 (không ghi đầu ra): khách trùng bàn, `reserved` sai công thức hoặc vượt tồn, bếp/tay cùng một đơn, món không khớp đơn, id bếp/bàn không tồn tại, `hand` sai schema, `gather.player.invuln_ticks` (PRD không có).
- [ ] `random_customers: false` không sinh khách; `random_fish: false` không có cá; thiếu khóa thì mặc định `true`.
- [ ] Ba module phụ rỗng được gọi từ `step()`; 32 test hiện có vẫn xanh.
