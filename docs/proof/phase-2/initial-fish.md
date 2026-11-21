# Kiểm chứng đàn cá đầu ca

- Lệnh: `python -m unittest discover -s tests -v` (môi trường Python có `python3`).
- Kết quả: 44 test đạt (`Ran 44 tests in 7.437s`, `OK`).
- Phạm vi: số lượng, vị trí không trùng, điểm sinh hợp lệ, seed, ID và scenario cá fixture.
- Test smoke cũ được đổi từ 6 sang 8 đàn vì ticket Phase 2 thay đổi số đàn ban đầu.
