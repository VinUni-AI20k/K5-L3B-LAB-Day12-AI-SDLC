# mhoo40 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - Phase 1–2 (`chonoi/sim/gather.py`, `tests/test_p2_lat2_fish.py`): hoàn thiện Lát 2 (hái nút, mọc lại, bắt cá, cá bơi 1.5 m/s, đổi hướng theo seed, phản xạ mép, sinh cá định kỳ), sửa lỗi tốc độ bơi chéo và cập nhật fixture test cũ (`00668ec`).
  - Phase 3 (`chonoi/sim/gather.py`, `tests/`): nâng cấp giỏ sang kho cá thể `{id, kind, fresh}` (v1.2), hao độ tươi 0.5/s, sự kiện `spoiled` một lần theo ID và migrate các test gather cũ.
  - Phase 4 (`chonoi/soak.py`, `tests/test_soak_p4.py`, `README.md`, `docs/proof/phase-4/clone-sach.txt`): viết `soak_cmd` chạy 10 Ngày tất định lặp chu kỳ D1–D5, cập nhật hướng dẫn chạy/kiểm thử và xác minh clone sạch.
- **Tôi đã review:**
  - Review tương thích Lát 0 v1.2 (`tests/test_lat0_v12.py`, `chonoi/items.py`) về làm tròn độ tươi khi xuất JSONL/file kho và PR tích hợp Phase 3.
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI sinh `_reflect_1d` truyền cả bước `speed / TICK` cho từng trục thay vì nhân với `|cos|` và `|sin|`, làm cá bơi chéo nhanh gấp $\sqrt{2}$ lần (~`2.086 m/s`). Nhóm phát hiện khi đo quãng đường thực tế 1500 tick và bổ sung test góc chéo `45°`.
- **Điều tôi học được:**
  - Test xanh trên biên thẳng chưa đủ đảm bảo tính chất vật lý; luôn cần kiểm thử trường hợp chéo/tổng quát và giữ thứ tự thực thi mỗi tick bám sát contract để tránh lệch giữa các module.