# Dấu ấn MMMMV — "Một ngày của Út Sen"

> Không cạnh tranh bằng số tính năng. Thắng bằng **một trải nghiệm liền mạch** và **cảm giác đúng chỗ**.
> Nguồn: bài học Wyatt Cheng (`~/research/wyatt-cheng/lessons.md`), PRD §2 "Tự do sáng tạo", rubric README.

## Nguyên tắc chọn

| Ô điểm | Cách ăn | Cách mất |
|---|---|---|
| Test ẩn 25 | lõi đúng 100%, không đổi schema/event/số | thêm "sáng tạo" vào sim → lệch byte |
| Chất lượng 10 | **một** ý tưởng gọn, làm tới cùng | 6 tính năng nửa vời |
| Demo 5 | 3 cảnh 20 giây ai cũng hiểu | giải thích bằng lời |

→ Luật tự đặt: **mọi thứ dưới đây không được chạm `chonoi/`**, trừ đúng một mục mở rộng có mã trong manifest (`net`).

## Sáu dấu ấn

| # | Dấu ấn | Cơ chế | Cảm giác | Chạm sim? | Người |
|---|---|---|---|---|---|
| 1 | **Nhịp thở buổi sáng** | Khi oxy < 25%: HUD nhấp nháy **nhanh dần theo %**, thêm tiếng tim + tối bốn rìa màn hình | nín thở | Không | Vinh |
| 2 | **Má Tư giao việc** | DayIntro 4 s + HUD "đã lấy 3/6" nằm cạnh giỏ | có mục tiêu, không lạc | Không (đọc `day_plan`) | Vinh |
| 3 | **Cá sống** | Đuôi ve vẩy theo pha riêng từng `id`, bóng mờ dưới đáy, vệt nước khi bơi | sông có cá thật | Không (chỉ đọc `pos`, `heading_deg`) | Vinh |
| 4 | **Thủy quái** | Viền tím + tiếng trầm + rung 2 px khi Cá Sấu trong 10 m | sợ thật | Không (đọc `monsters[]`) | Vinh |
| 5 | **Khách có mặt** | Mắt/miệng đổi theo `patience_ticks_left`, bong bóng món nhấp nhô, run tay khi < 25% | khách là người | Không | Vinh |
| 6 | **Một đồng hồ** | `DayClock` từ `tick`/`time_left_ticks` lái palette sáng → trưa → đêm cho cả ba pha | một ngày trôi | Không | Vinh |

Mỗi hiệu ứng phải có **fallback**: thiếu trường trong snapshot thì vẽ trạng thái trung tính, không văng lỗi.

## Ba luật keo (quan trọng hơn danh sách)

1. **Một đồng hồ, nhiều người nghe.** Palette, vignette, tông nhạc, tốc độ trôi của ghe đều là hàm của cùng một `t01 = 1 - time_left_ticks/duration`. Không thành phần nào tự đếm giờ.
2. **Không đi trước sim.** Hình và tiếng trễ sau dữ liệu 60–120 ms, không suy diễn ra ngoài snapshot. Người chơi phải tin màn hình.
3. **Cái gì kêu thì phải có cái thấy.** Mỗi âm thanh buộc một hiệu ứng hình trong ±100 ms.

## Muối, không phải muối biển

- Rung màn hình: 2–3 px, 80 ms, đúng **4** khoảnh khắc (cập bến, bắt cá, khách trả tiền, bị ngạt).
- Có `?fx=0` tắt hiệu ứng nặng, `M` tắt tiếng — vì người chơi xin tắt là yêu cầu hợp lý.
- Nếu một hiệu ứng không nhìn thấy được trong ảnh chụp màn hình tĩnh thì nó **không** thuộc về demo.

## Bằng chứng phải có (cho README "Sáng tạo của nhóm")

1. Ảnh trước/sau của cùng một cảnh (không hiệu ứng / có hiệu ứng).
2. Video 20 s mỗi cảnh: lặn + hết hơi; bị Cá Sấu cắn; khách sắp bỏ đi rồi được phục vụ.
3. Một dòng chứng minh lõi không đổi: `python3 tools/run_checks.py` xanh **trước và sau** khi thêm hiệu ứng.
4. Ghi rõ: mọi thứ trong mục này chạy ở client, headless không đổi một byte.

## Điều sẽ KHÔNG làm (dù hay)

| Ý tưởng | Vì sao không |
|---|---|
| Túi bi / pity cho món khách gọi | PRD bắt "chọn đều theo seed" ở lõi → lệch hidden test |
| Thời tiết/thủy triều ảnh hưởng luật | sửa `step()` cả hai sim, rủi ro cao, lợi ích thấp hơn `net` |
| Thêm 6 món ngoài kế hoạch | PRD cố định ID và công thức |
| Asset ngoài, engine khác | vi phạm quy định, mất tính "1 file mở là chạy" |
