# Kiểm chứng Cá Sấu

- Lệnh: `python -m unittest discover -s tests` (môi trường Python có `python3`).
- Kết quả: 116 test đạt (`Ran 116 tests in 12.040s`, `OK`).
- Phạm vi test mới: tuần tra/đuổi, va chạm nhiều Cá Sấu, rơi hàng LIFO, bất tử, recoil 60 bước, ngạt cùng tick, ngất, scenario sai và bố trí gather Ngày 1.
- Sau khi merge `origin/main` vào nhánh Cá Sấu: 131 test đạt (`Ran 131 tests in 12.955s`, `OK`). Vòng ngày đã có trong nhánh tích hợp, nhưng chưa truyền số ngày vào `GatherSim` để bật M2 từ Ngày 3.
- Sau khi truyền ngày vào `GatherSim`: 133 test đạt (`Ran 133 tests in 12.006s`, `OK`); kiểm tra Ngày 1–2 có M1, Ngày 3 có M1/M2 và scenario Cá Sấu thay thế danh sách mặc định.
