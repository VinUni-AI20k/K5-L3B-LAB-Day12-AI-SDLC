# Kiểm tay Phase 1 — chơi được hai buổi, HUD (DoD 1)

- **Thời điểm:** 2026-11-21, nhánh `qa/phase1-verification` (đã gộp `dev` với PR #3, #4, #5, #6).
- **Người kiểm:** czx04 (QA), thực hiện qua Claude Code điều khiển trình duyệt tích hợp. Phím được gửi bằng sự kiện bàn phím vào trang, trạng thái đọc từ `GET /state` của `chonoi.live`.
- **Lệnh:**
  ```bash
  python3 -m chonoi.live --mode gather --seed 1 --inventory-out kho.json
  python3 -m chonoi.live --mode quan --seed 1 --inventory kho.json
  ```

## Buổi sáng (`gather`)

| Bước | Quan sát | Kết quả |
|---|---|---|
| Mở game | HUD có đồng hồ (2:55), thanh oxy, 3 Máu, nút N1–N4, đàn F1–F6, giỏ 0/12 | đạt |
| Giữ D rồi S, lặn tới F1 `[15,5]` | Oxy giảm (1800 → 1725 tick), thanh "Oxy 27s"; dòng sự kiện `dive` | đạt |
| Space cạnh F1 | `fish_caught` F1 ca_linh yield 3; giỏ 3 cá linh; F1 biến mất | đạt |
| Giữ W lên mặt nước, A tới N1, E | Oxy hồi đầy (→ 1800); `gather` N1 bong_dien_dien amount 1; giỏ 4/12 | đạt |
| A về bến, E | Màn "Buổi sáng kết thúc: docked"; `kho.json` = `{"items":{"bong_dien_dien":1,"ca_linh":3}}` | đạt |

Ảnh: [đang lặn](manual/gather-dang-lan.png) · [cập bến](manual/gather-cap-ben.jpg)

## Buổi tối (`quan`, kho từ buổi sáng)

| Bước | Quan sát | Kết quả |
|---|---|---|
| Mở game | HUD: đồng hồ, "Tiền 0k · uy tín 3.0 · điểm 300", "Kho: điên điển×1, cá linh×3" | đạt |
| Chờ khách | `customer_arrived` C1 → T1, món `lau_ca_linh_dien_dien` (món duy nhất đủ nguyên liệu), nhãn món + trạng thái trên bàn, thanh kiên nhẫn đỏ dưới khách | đạt |
| Tới B1, E | `cook_started`; kho → (trống); vòng tiến độ nấu quanh B1; đơn `assigned` | đạt |
| Đợi 10 s, E ở bếp | `dish_ready` rồi `dish_picked`; tay cầm `{order_id: C1, dish_id: lau_ca_linh_dien_dien, base_price: 120}`; bếp `idle` | đạt |
| Tới T1, E | `served`; khách `eating`; kiên nhẫn còn 871/3600 (< 50%) nên boa 0 | đạt |
| Đợi 10 s | Khách trả tiền và rời bàn: tiền 120k, earned 120, uy tín 3.0, điểm 420 (= 120 + 100 × 3) | đạt |

Ảnh: [đang nấu](manual/quan-dang-nau.jpg) · [khách đang ăn](manual/quan-khach-an.jpg)

## Ghi nhận / chưa kiểm

- **Lỗi hiển thị nhỏ (gather):** ở cửa sổ cao, dòng "Giỏ 4/12 …" ở góc dưới trái đè lên dòng hướng dẫn phím ở góc dưới phải (xem ảnh cập bến). Vẫn đọc được số giỏ. Báo `client/ui` (itsbra1vo).
- **Thanh kiên nhẫn** nhỏ (rộng ~1.6 ô), không có số; đọc được nhưng khó nhìn từ xa.
- Ảnh chụp có thể trễ vài khung hình so với `/state` (canvas vẽ theo `requestAnimationFrame`), không ảnh hưởng luật.
- **Chưa kiểm trong lần này:** ngạt/mất Máu/ngất trên UI, `hold_full`, khách bỏ về vì hết kiên nhẫn (−0.5 uy tín), boa dương, phím R. Các luật này đã có test tự động (xem ma trận truy vết).

**Kết luận DoD 1:** chơi được cả hai buổi và nối qua file kho; HUD hiển thị đủ các mục PRD yêu cầu (thời gian, oxy, Máu, giỏ; kho khả dụng, món gọi, kiên nhẫn, trạng thái bếp, món trên tay, tiền, uy tín). Có 1 lỗi hiển thị nhỏ ở trên.
