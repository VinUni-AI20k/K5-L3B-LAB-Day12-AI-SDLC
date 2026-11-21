# Kiểm chứng sinh cá

- Lệnh: `python -m unittest discover -s tests -v` (môi trường Python có `python3`).
- Kết quả: 52 test đạt (`Ran 52 tests in 7.533s`, `OK`).
- Phạm vi: lịch 360 tick, giới hạn đàn, seed, điểm cách đàn sống hơn 1 m, loài còn điểm hợp lệ, vị trí sau khi bơi và không sinh khi tắt hoặc hết giờ.
- Khi tích hợp pause/day, chỉ gọi `GatherSim.step` cho bước gameplay để `phase_tick` không tăng khi tạm dừng.
