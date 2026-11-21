# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Gather — Ngất đúng tick biên | Kiểm thứ tự sự kiện tick 1, giỏ rơi theo LIFO và kho rỗng | [QA Phase 1](../proof/phase-1/qa.md) | Đạt trên main (fdc986b). |
| Test Contract — Fixture không hợp lệ | `player.hp=0` trả mã 2 và giữ nguyên hai file đầu ra | [QA Phase 1](../proof/phase-1/qa.md) | Đạt trên main (fdc986b). |
| Gather → Quán — Chuyển kho | Smoke seed 42 chạy hai tiến trình và đối chiếu kho ở snapshot tick 0 | [QA Phase 1](../proof/phase-1/qa.md) | Đạt trên main (fdc986b). |
| Quán — Phục vụ đúng hạn và đóng ca | Chạy các ca phục vụ ở tick biên và kiểm lý do kết thúc ca trong `tests/test_quan.py` | [Bằng chứng Quán](../proof/phase-1/quan-sim.md) | Đạt trên main (fdc986b). |

## Đánh giá ngắn

- Bản tích hợp `main` tại `fdc986b` đạt 45/45 test trên Windows PowerShell với Python 3.11.9.
- Hai ca QA bổ sung đều đạt: ngất đúng tick biên và giữ nguyên file đầu ra khi fixture không hợp lệ.
- Smoke chuyển kho gather → quán, ca phục vụ đúng tick biên và ca đóng quán đều đạt.
