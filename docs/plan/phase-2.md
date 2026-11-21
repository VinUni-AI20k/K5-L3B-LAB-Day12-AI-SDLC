# Kế hoạch Kỹ thuật Phase 2 — Một Ngày Ở Chợ Nổi (Test Contract v1.1)

> **Mã Ticket:** `TICKET-02`  
> **Thời lượng quy định:** 55 phút · **Hạn chốt tag:** `phase-2`  
> **Contract Version:** `1.1`  
> **Chế độ mới:** `--mode day` (chạy trọn vẹn 1 đến 5 ngày)

---

## 1. MỤC TIÊU CỐT LÕI PHASE 2
Nối thông 2 buổi Sáng (`gather`) và Tối (`quan`) thành một vòng ngày hoàn chỉnh:
$$\text{DayIntro} \longrightarrow \text{gather} \longrightarrow \text{EveningIntro} \longrightarrow \text{quan} \longrightarrow \text{DayResult} \longrightarrow \text{Shop} \longrightarrow \text{Day kế tiếp}$$

1. **Sáng:** Má Tư công bố kế hoạch món ăn D1..D5. Út Sen lặn lòng sông Mekong, đối mặt đàn cá bơi tuần tra thật sự và thủy quái **Cá Sấu Năm Chèo**.
2. **Tối:** Quán mở với nguyên liệu mang về, phục vụ 4 bàn ăn, 2 bếp than hồng, thực đơn 6 món.
3. **Cuối ngày:** Mở Shop dùng tiền tích lũy mua nâng cấp Bình Oxy (45s, 60s) và Áo phao (4 HP, 5 HP) áp dụng cho ngày hôm sau.

---

## 2. PHÂN CÔNG 4 LÁT CẮT KỸ THUẬT (5 DEV)

### Lát 1: Sinh Thái & Săn Bắt Cá v1.1 (DEV 2 — Tuấn phụ trách)
- **Nông sản mới:** Bổ sung Bông Kèo Nèo (`keo_neo` tại N5 `[76, 0]`, N6 `[90, 0]`).
- **Thủy sản mới:** Bổ sung Cá Kèo (`ca_keo`, sản lượng yield = 2).
- **Động vật di chuyển trong sim (Fish Swimming AI):**
  - Vận tốc $1.5$ m/s trong $x \in [4, 96]$.
  - Tầng nước: Cá Linh $d \in [3, 12]$, Cá Lóc $d \in [8, 20]$, Cá Kèo $d \in [22, 28]$.
  - Đổi hướng tuần tự theo RNG stream `Streams` ở các bước 120, 240, 360... trước khi di chuyển.
  - Chạm mép sông: phản xạ phần quãng đường còn lại và đảo thành phần hướng vuông góc với mép (chạm góc đảo cả hai).
- **Sinh cá theo lịch (Fish Spawning Scheduler):**
  - Khởi đầu ca: 8 đàn tại 8 điểm sinh khác nhau; trần tối đa 12 đàn.
  - Tại `phase_tick = 360 * k` ($k \ge 1$), sinh tối đa 1 đàn nếu dưới trần 12 và có điểm cách các đàn đang sống $> 1.0$m.
  - Tỉ lệ phân bổ loài: Cá Linh 40%, Cá Lóc 30%, Cá Kèo 30%.
- **Bắt cá v1.1:** Cần đủ chỗ trống trong giỏ cho cả đàn (Cá Linh 3, Cá Lóc 1, Cá Kèo 2); nếu thiếu chỗ bắn `hold_full` và cá không bị mất.

### Lát 2: Thủy Quái Cá Sấu & Sinh Tồn (DEV 1)
- **Thủy quái Cá Sấu Năm Chèo:**
  - M1 xuất hiện từ Ngày 1 (tuần tra `[60, 24] <-> [64, 24]`).
  - M2 xuất hiện từ Ngày 3 (tuần tra `[85, 18] <-> [89, 18]`).
  - Tuần tra 1.0 m/s; khi người chơi ở $d \ge 10$ và cách $\le 10$m $\implies$ chuyển `chase` bơi rượt đuổi ở 3.0 m/s.
  - Rời đuổi khi cách $> 16$m hoặc người chơi bơi lên $d < 10$.
- **Cơ chế Cắn Táp & Rơi đồ (Hit & Drop):**
  - Khoảng cách $\le 1.5$m, $d \ge 10$ và hết bất tử: mất 1 HP, rơi $\lfloor \text{hold} / 2 \rfloor$ nguyên liệu theo LIFO.
  - Bất tử 90 ticks. Cá sấu recoil lùi 60 bước theo hướng ngược người chơi.
  - Máu = 0 $\implies$ Ngất (`fainted`), mất sạch giỏ đồ, quán mở tối với kho rỗng.

### Lát 3: Quán Ăn Chợ Nổi v1.1 (DEV 3 & DEV 4)
- Mở rộng 2 Bếp nấu (B1 `[2, 8]`, B2 `[5, 8]`) và 4 Bàn ăn (T1 `[9, 2]`, T2 `[13, 2]`, T3 `[9, 6]`, T4 `[13, 6]`).
- Thực đơn 6 món: bổ sung Canh chua cá lóc (90 xu), Cá kèo nướng muối ớt (70 xu), Lẩu mắm miền Tây (200 xu).
- Khách đến theo kế hoạch thực đơn của Má Tư (D1..D5) trong chế độ Day.

### Lát 4: Vòng Lặp Day, Shop & Tạm Dừng (DEV 5 & FE/Chung)
- CLI Runner: Hỗ trợ `--mode day --days <1..5>`.
- Chế độ Shop: Mua nâng cấp Bình Oxy (Cấp 1: 200 xu $\to$ 45s, Cấp 2: 400 xu $\to$ 60s) và Áo phao (Cấp 1: 250 xu $\to$ 4 HP, Cấp 2: 500 xu $\to$ 5 HP). Đóng bằng phím `shop_done` hoặc timeout 600 ticks.
- Cơ chế Tạm dừng (Pause): Phím `Esc` / `P` dừng mọi timer và đồng hồ gameplay.
- Giao diện Web: Cập nhật HUD hiển thị kế hoạch Má Tư, Thủy quái cảnh báo viền tím, shop mua sắm cuối ngày.

---

## 3. LỘ TRÌNH TRIỂN KHAI PHASE 2 TỪNG BƯỚC

1. **Bước 1:** Nâng cấp Contract data trong `game.contract.json` lên v1.1 (thêm tuning cá bơi/sinh, cá sấu, 6 món, shop, day_plan).
2. **Bước 2:** Triển khai Lát 1 trong `chonoi/sim/gather.py`: Node Kèo nèo N5/N6, Cá Kèo yield 2, cá bơi tuần tra, phản xạ mép, sinh cá định kỳ. Viết unit test cho Lát 1.
3. **Bước 3:** Triển khai Lát 2: Cá Sấu Năm Chèo M1/M2, rượt đuổi, táp mất máu, rơi nửa giỏ LIFO, ngất.
4. **Bước 4:** Triển khai Lát 3: 2 Bếp, 4 Bàn, 6 Món và tích hợp kế hoạch Má Tư.
5. **Bước 5:** Triển khai Lát 4: Bộ điều khiển chế độ Day (`runner.py` / `day.py`), Shop mua sắm, cơ chế pause, đồng bộ Web HUD.
6. **Bước 6:** Chạy smoke test, kiểm tra tính tất định byte-for-byte v1.1, ghi bằng chứng vào `docs/verification/phase-2.md`, commit và đẩy tag `phase-2`.
