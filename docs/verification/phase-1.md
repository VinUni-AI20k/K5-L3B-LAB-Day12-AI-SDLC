# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Gather — Ngất đúng tick biên | Kiểm thứ tự sự kiện tick 1, giỏ rơi theo LIFO và kho rỗng | [QA Phase 1](../proof/phase-1/qa.md) | Đạt trên `cecbe8e` với test QA. Chờ kiểm trên bản tích hợp. |
| Test Contract — Fixture không hợp lệ | `player.hp=0` trả mã 2 và giữ nguyên hai file đầu ra | [QA Phase 1](../proof/phase-1/qa.md) | Đạt trên `7a3292b` và `cecbe8e` với test QA. |
| Gather → Quán — Chuyển kho | Smoke seed 42 chạy hai tiến trình và đối chiếu kho ở snapshot tick 0 | [QA Phase 1](../proof/phase-1/qa.md) | Đạt trên bản đã kiểm thử. |
| Quán — Phục vụ đúng hạn và đóng ca | Chạy các ca phục vụ ở tick biên và kiểm lý do kết thúc ca trong `tests/test_quan.py` | [Bằng chứng Quán](../proof/phase-1/quan-sim.md) | Đạt trong suite 43/43 trên `cecbe8e` với test QA. |

## Đánh giá ngắn

- Nhánh gather `cecbe8e` cùng hai ca QA bổ sung đạt 43/43.
- Chạy lại full suite sau khi gather được tích hợp, rồi cập nhật SHA và kết quả của bản bàn giao.
