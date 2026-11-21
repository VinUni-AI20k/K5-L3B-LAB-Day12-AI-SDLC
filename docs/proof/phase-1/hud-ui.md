# Bằng Chứng Kiểm Chứng HUD & UI (Ticket 06 — Phase 1)

> **Người thực hiện:** Tào Quang Vinh (`@qvinhh2312` — UX + Demo lead)  
> **Module:** `client/ui` (`chonoi/web/index.html`)  
> **Ticket:** `docs/tickets/phase-1/06-hud.md`

---

## 1. Ma trận tiêu chí chấp nhận (Acceptance Criteria)

| Mã AC | Tiêu chí trong Ticket 06 | Hiện thực trong `chonoi/web/index.html` | Kết quả |
|---|---|---|:---:|
| **AC-01** | **Buổi sáng (Gather):** Thời gian còn lại, thanh oxy đổi màu khi gần cạn, Máu (HP), số món/capacity, danh sách giỏ hàng. | Top bar hiện đồng hồ ⏱ (chuyển đỏ khi < 30s), thanh Oxy 3 dải màu (đỏ < 25%), Máu ♥♥♥, giỏ hàng trực quan từng slot + tên loài & số lượng. | **ĐẠT** |
| **AC-02** | **Nhắc phím ngữ cảnh buổi sáng:** Vào tầm bến tàu, nút rau, đàn cá. | Banner in-canvas bo góc viền vàng hiển thị: `[E] Cập bến`, `[E] Hái <cây>`, `[Space] Bắt đàn <cá>` (kèm cảnh báo giỏ đầy / hồi chiêu). | **ĐẠT** |
| **AC-03** | **Buổi tối (Quán):** `stock` kho nguyên liệu, khách ngồi kèm món gọi + thanh kiên nhẫn, bếp + thời gian nấu, món trên tay, tiền, uy tín, thời gian. | Bottom panel hiện `Kho dự trữ`, bàn ăn hiện khách + thanh kiên nhẫn đổi màu (xanh/vàng/đỏ), bếp hiện đếm ngược giây/ready, top bar hiện tiền, sao uy tín, điểm và món trên tay. | **ĐẠT** |
| **AC-04** | **Nhắc phím ngữ cảnh buổi tối:** Vào tầm bếp hoặc bàn ăn. | Banner ngữ cảnh hiện nhắc: `[E] Bắt đầu nấu`, `[E] Bưng món`, `[E] Phục vụ bàn <id>` (báo lỗi nếu món trên tay không khớp đơn). | **ĐẠT** |
| **AC-05** | **Xử lý thiếu trường (Null-safety):** Không văng lỗi khi luật chưa xong. | Toàn bộ truy xuất dùng toán tử an toàn `?.`, `??`, fallback mảng rỗng `[]`, kiểm tra `undefined`, bọc `try/catch` vòng lặp vẽ. | **ĐẠT** |
| **AC-06** | **Bố cục thoáng, không che vùng chơi:** | HUD neo sát viền mép trên/dưới dạng thanh bar trong suốt nhẹ (`glassmorphism`), alpha lớp trang trí thấp, vùng chơi chính giữa hoàn toàn thông thoáng. | **ĐẠT** |
| **AC-07** | **Màn kết thúc (Game Over Overlay):** Hiện lý do (`docked`/`time`/`fainted`), điểm số, nút chơi lại. | Modal bo góc lớn giải thích rõ ràng từng lý do kết thúc, bảng thống kê sản lượng/tiền/uy tín/điểm, nút bấm `[Chơi lại]` hỗ trợ cả click chuột và phím R. | **ĐẠT** |
| **AC-08** | **Không đụng mã `chonoi/sim/`:** Giữ nguyên tính tất định của headless. | Không sửa bất kỳ tệp Python nào trong `chonoi/sim/`, headless mode chạy độc lập với giao diện web. | **ĐẠT** |

---

## 2. Lệnh kiểm chứng thực tế

### 2.1. Kiểm thử giao diện chơi trực tiếp (Live Mode)
```bash
# Chơi thử buổi sáng (Lặn & Hái)
python3 -m chonoi.live --mode gather

# Chơi thử buổi tối (Quán ăn)
python3 -m chonoi.live --mode quan
```
*Kết quả:* Trình duyệt mở tại cổng localhost được cấp; các thao tác WASD, E, Space, R phản hồi tức thì; thanh Oxy và kiên nhẫn đổi màu chính xác; banner nhắc phím bật/tắt đúng bán kính tương tác.

### 2.2. Kiểm thử tính bất biến của Headless (Contract Invariance)
```bash
python3 -m chonoi.headless --mode gather --seed 1 --ticks 180 --out out_test.jsonl
```
*Kết quả:* File JSONL sinh ra đúng chuẩn contract v1.0, không có bất kỳ sai lệch nào về snapshot hoặc event.
