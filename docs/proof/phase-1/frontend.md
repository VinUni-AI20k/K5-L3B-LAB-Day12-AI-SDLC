# Phase 1 — Phần 5: Game Frontend

Kiểm tra trên nhánh `feat/frontend` ngày 21/11/2026.

## Phạm vi

- `chonoi/web/index.html`: thay hình khối tạm và log JSON của starter bằng hai cảnh Canvas 2D, HUD tiếng Việt và thông báo sự kiện. Sửa phần gửi phím và chơi lại để giữ thứ tự POST, xử lý mất focus và tránh dùng snapshot cũ sau khi restart. Trang đọc thời gian và kết quả từ `/state`.
- `CREDITS.md`: ghi nguồn minh họa Canvas và biểu tượng SVG do nhóm tạo với Codex.
- Hai scenario và ảnh dưới đây dùng để tái hiện trạng thái giao diện. Server, sim, contract, schema kho và test của nhóm giữ nguyên.

## Chạy lại

```powershell
$env:PYTHONPATH = 'tests;.'
python -m unittest discover -s tests -v
```

Kết quả: **32 test qua**. Kiểm tra cú pháp script bằng Node cũng qua.

Chạy mỗi lệnh ở một terminal và mở URL tương ứng:

```powershell
python -m chonoi.live --mode gather --port 8761
python -m chonoi.live --mode quan --port 8762
python -m chonoi.live --mode gather --port 8763 --scenario docs/proof/phase-1/frontend-gather.json
python -m chonoi.live --mode quan --port 8764 --scenario docs/proof/phase-1/frontend-quan.json
```

## Bằng chứng trình duyệt

| Hạng mục | Kết quả quan sát trong Chrome |
|---|---|
| API và điều khiển | Buổi sáng có chiều xuống là +d, buổi tối có chiều lên là +z. Sim về vận tốc 0 sau blur, tải lại trang khi đang di chuyển và lỗi đọc `/state` còn ghi được `/input`. Hai POST cho một lần nhấn rồi nhả Space đi theo thứ tự. Space và Enter khi focus nút kích hoạt chơi lại. E ở bến kết thúc buổi thật và R mở lượt mới. Quán mặc định trả reason `time` khi hết giờ. |
| Gather với scenario | Giỏ 12/12, cá linh ×4 trong thống kê, Máu 2/3, oxy 5s/30s và cảnh báo chữ. Chơi lại để thấy hồi bắt và cây đang mọc lại; khi hồi bắt hết, báo giỏ không đủ chỗ gần cá. [1440 × 900](frontend-gather-1440.jpg) · [390 × 844](frontend-gather-390.jpg). |
| Quán với scenario | Bếp B1 đếm ngược 4s và đọc tên lẩu từ `dish.dish_id`; bàn T1 có đơn và thanh kiên nhẫn 11s. Kho hiển thị cá linh 3 từ 6 trừ 3, bông điên điển 1 từ 2 trừ 1, bông súng 0. Mặc định hiển thị bếp trống và chưa có khách gọi món. [1440 × 900](frontend-quan-1440.jpg) · [390 × 844](frontend-quan-390.jpg). |
| Phản hồi và dữ liệu biên | Qua lớp giả lập phản hồi riêng trong Chrome: loading, mất kết nối, HTTP 503 ở GET và các POST, lỗi sim, ngất, món trên tay dạng object, bếp xong, khách đang ăn không còn thanh kiên nhẫn, kho thiếu hiển thị `—`, giỏ đổi sang 5 ô, gợi ý hái/bắt theo snapshot, offset bounds và hai event cùng tick chỉ hiện mỗi event một lần. |
| Bố cục | Cả hai cảnh qua phép đo ở 1440×900, 1366×768, 1024×768 và 390×844. HUD/thông báo/khay tách khỏi Canvas, không tràn ngang. Canvas có backing store đúng DPR 1 ở desktop và DPR 2 tại 390 px. Không ghi nhận lỗi JavaScript hoặc asset 404 trong lượt chạy. |

Design Taste Frontend được dùng để rà bố cục, tương phản và phản hồi nút. Gate báo `GATE: FAIL 25 (round 1 of 3)`, với 13 cảnh báo. Các nhóm lỗi gồm hero toàn màn hình, CTA cuối trang, section theo chiều cao viewport, hiệu ứng quảng bá và quy tắc canh lề/heading dành cho landing page. Phép kiểm giao diện tương tác dùng bảng trên thay cho tiêu chí landing page.

### Cập nhật pixel art

Hai cảnh được vẽ trên lưới pixel rồi phóng nguyên khối, với chữ HUD và nhãn Canvas ở độ phân giải đầy đủ. Cảnh Quán có thêm bờ sông, nhà sàn lên đèn và trăng phản chiếu ngoài vùng đi lại.

Ảnh mới nhất thể hiện hướng mỹ thuật lấy cảm hứng từ không khí ấm áp của Stardew Valley: HUD màu giấy đóng khung gỗ, ván bè nhuộm ánh đèn, sprite tự vẽ cho Út Sen, khách, cá và hoa. Giỏ dùng biểu tượng lấy từ cùng bộ sprite.

Đã kiểm bằng Chrome trên cả hai scenario ở 1440×900, 1366×768, 1024×768 và 390×844. Mẫu ảnh xác nhận các khối pixel không bị nội suy, Canvas đúng DPR và trang không tràn ngang. Cả 12 biểu tượng trong giỏ scenario tải được. Đã kiểm di chuyển, chơi lại và kho khả dụng. Không ghi nhận lỗi JavaScript hoặc HTTP. Copy lint của Design Taste Frontend trả 0 lỗi, 0 cảnh báo. [Ảnh Gather](frontend-pixel-gather.png) · [Ảnh Quán](frontend-pixel-quan.png).

Sau phản hồi về độ nét, frontend dùng lưới mịn hơn cho nền, vẽ sprite ở lớp riêng theo khối pixel nguyên và đặt nhãn Út Sen ngoài vùng sprite. Cảnh Gather chuyển sắc độ nước theo độ sâu và có nét dừa nước rõ hơn. Kiểm lại bốn kích thước trên trong Chrome ở DPR 1, 1,25 và 2. Màu các pixel đục trên sprite Út Sen khớp với sprite gốc trong hai scenario. 32/32 test Python qua.

## Phụ thuộc tích hợp

1. **Người 1 — sinh tồn:** cần oxy hồi/hao, sát thương do ngạt và ngất từ sim. Oxy thấp và Máu đã xem qua scenario; chưa kiểm được chuỗi sự kiện sinh tồn từ đầu đến cuối.
2. **Người 2 — thu thập/kho:** cần hái, bắt cá, sức chứa sau hành động và payload sự kiện thật. Đã kiểm cập bến thật; dùng phản hồi giả lập để kiểm UI của sự kiện hái/bắt.
3. **Người 3 — khách/đặt chỗ:** cần vòng đời khách, giữ chỗ, giảm kiên nhẫn và kiểm không giữ chỗ quá kho. Đã kiểm kho khả dụng và đơn hàng bằng scenario.
4. **Người 4 — bếp/phục vụ:** cần các chuyển trạng thái nấu, cầm, phục vụ và thanh toán. Đã kiểm payload món, countdown đang nấu và các trạng thái hiển thị bằng scenario/phản hồi giả lập. Cần chạy lại các luồng thực và đối chiếu tên trường cùng mã lý do của event khi tích hợp.
