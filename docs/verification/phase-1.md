# Ma trận truy vết Phase 1 (Quán Ăn Chợ Nổi)

> Tag bàn giao: `phase-1`  
> Thời điểm xác thực: 21/11/2026  
> Trạng thái test suite: 44/44 test cases PASS (100%)

| AC | Nội dung yêu cầu | Cách kiểm chứng | Bằng chứng / File log | Kết quả |
| :---: | :--- | :--- | :--- | :---: |
| **AC-P1-01** | Bơi, ramp gia tốc, kẹp mép sông `[0, 100]` và `[0, 30]`, d không âm | `tests/test_smoke_p1.py::Movement` | 6 unit tests về swim_speed, edge_clamp, ramp | **ĐẠT** |
| **AC-P1-02** | Tính tất định byte-for-byte theo seed (Contract Con-02) | `test_con_02_deterministic_bytes` | Output nhị phân 2 lượt chạy trùng khớp 100% | **ĐẠT** |
| **AC-P1-03** | Hái hoa Bông Điên Điển & Bông Súng tại mặt nước ($d \le 0.5$) | `tests/test_dev2_harvest_catch.py::TestHarvestMechanics` | 4 test cases (thành công, chặn dưới nước, giỏ đầy, mọc lại sau 1200 tick) | **ĐẠT** |
| **AC-P1-04** | Săn bắt Cá Linh (yield 3) & Cá Lóc (yield 1) dưới nước ($d > 0.5$) | `tests/test_dev2_harvest_catch.py::TestCatchMechanics` | 8 test cases (hồi chiêu 30 tick, tie-break `id_key`, partial yield tại 11/12, giỏ đầy) | **ĐẠT** |
| **AC-P1-05** | Bàn giao giỏ đồ LIFO sang kho quán ăn buổi tối (`gather` $\to$ `quan`) | `test_inv_01_gather_writes_inventory_quan_reads_it` | Ghi nguyên tử `inventory.json`, quán đọc kho đúng số lượng | **ĐẠT** |
| **AC-P1-06** | Đồ họa Web Canvas 2.5D Dave the Diver Mekong & WebAudio SFX | Mở `chonoi.live --mode gather` cổng 8000 | DOM HUD 12 slot, camera LERP, cá bơi lội tuần tra, phản xạ né | **ĐẠT** |

## Đánh giá ngắn
- **Yêu cầu đạt:** Toàn bộ 44/44 test suite xanh lá. Cơ chế hái hoa, hồi chiêu bắt cá, partial yield 11/12, giỏ đồ LIFO, và đồ họa Web 2.5D Mekong hoàn thành vượt mong đợi.
- **Điều cần chỉnh cho Phase 2:**
  - Nâng cấp Contract v1.1 theo `PHARSE2.md`.
  - Bổ sung chế độ `--mode day` (vòng lặp trọn ngày từ Ngày 1 đến Ngày 5).
  - Tích hợp động vật di chuyển trong sim (Cá bơi 1.5 m/s, Thủy quái Cá Sấu Năm Chèo M1/M2 rượt đuổi, cắn mất máu và rơi đồ).
  - Mở rộng menu 6 món và hệ thống Shop nâng cấp (Bình Oxy, Áo Phao).
