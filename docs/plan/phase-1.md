# Kế hoạch Phase 1

Mục tiêu là chơi được Lặn & Hái và Mở Quán theo Test Contract v1.0, nối qua [file kho](../contracts/README.md) và kiểm chứng trên `main` trước khi gắn `phase-1`.

| AC | Việc | Người | Phụ thuộc |
|---|---|---|---|
| AC-P1-01 | Bơi, oxy, Máu, ngất, biên và giỏ | Diên | Tuning preset và snapshot gather |
| AC-P1-02 | Hái, bắt, cập bến và bàn giao | Diên | AC-P1-01 và schema kho |
| AC-P1-03 | Khách, chọn món, giữ nguyên liệu và kiên nhẫn | Nhân | Mẫu kho và tuning preset |
| AC-P1-04 | Nấu, bưng, phục vụ, trả tiền, boa và uy tín | Nhân | AC-P1-03 |
| AC-P1-05 | HUD cả hai ca và hướng dẫn chạy, test, điều khiển | Khôi | Snapshot đã chốt, dùng fixture để làm song song |
| AC-P1-06 | Smoke hai tiến trình, kiểm fixture sai, tính tất định và lập bằng chứng | Khôi | Hai lát đã gộp vào `main` |

Các nhánh là `phoenix/p1-gather`, `phoenix/p1-quan` và `phoenix/p1-hud`. Rà vướng ở phút 20. Khi một bước cần PR phụ thuộc, chờ SHA bàn giao, pull `main` rồi kiểm lại trước khi tiếp tục. Ghi kết quả thực tế trong [ma trận](../verification/phase-1.md) và lưu bằng chứng ở `docs/proof/phase-1/`.
