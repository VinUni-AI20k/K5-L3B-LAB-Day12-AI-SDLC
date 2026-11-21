# Kiểm chứng cá bơi

- Lệnh: `python -m unittest discover -s tests -v` (môi trường Python có `python3`).
- Kết quả: 48 test đạt (`Ran 48 tests in 7.681s`, `OK`).
- Phạm vi: tốc độ, đổi hướng theo seed, phản xạ ở mép/góc, cá fixture đứng yên, bắt trước khi cá bơi và không bơi sau khi hết giờ.
- Fixture trong test bắt cá được đặt `random_fish: false` vì Phase 2 mặc định cá bơi; mục đích là giữ nguyên vị trí để kiểm tra riêng luật bắt.
