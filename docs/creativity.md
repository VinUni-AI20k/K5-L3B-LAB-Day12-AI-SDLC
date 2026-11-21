# Nội Dung Đề Xuất Mục "Sáng Tạo Của Nhóm" (Cho README.md)

> **Tài liệu do Vinh (UX + Demo lead) biên soạn để bạn hoặc Đức Minh đưa vào `README.md` mục "Sáng tạo của nhóm".**

---

```markdown
## Sáng tạo của nhóm (Team MMMMV)

Ngoài các yêu cầu cơ bản trong PRD-0, nhóm MMMMV đã nghiên cứu và phát triển thêm các tính năng nâng cao trải nghiệm người chơi (UX), đồ họa và âm thanh sống động:

1. **Giao diện HUD Thông Minh & Trực Quan (UX Canvas HTML5):**
   - Thiết kế dạng panel kính mờ (`glassmorphism`), phân tầng thông tin rõ ràng ở mép màn hình, không che khuất khu vực điều khiển và tương tác của nhân vật.
   - Thanh Oxy chuyển đổi mượt mà giữa 3 trạng thái màu (Xanh biển $\rightarrow$ Cam $\rightarrow$ Đỏ rực nhấp nháy cảnh báo khi cạn $< 25\%$).
   - Thanh Kiên nhẫn của khách đổi màu động theo thời gian chờ (Xanh lá $\rightarrow$ Vàng $\rightarrow$ Đỏ khi sắp bỏ đi).
   - Banner nhắc phím ngữ cảnh tương tác thông minh (Contextual Prompts): Nhắc `[E] Cập bến`, `[E] Hái <cây>`, `[Space] Bắt cá`, `[E] Nấu/Bưng món` khi người chơi đi vào đúng phạm vi tương tác.
   - Màn hình kết thúc ca chơi (Game Over Overlay): Thống kê chi tiết thành tích (sản lượng, doanh thu, uy tín, điểm số), hiển thị nguyên nhân kết thúc rõ nghĩa (`docked`, `time`, `fainted`), tích hợp nút bấm Chơi lại trực quan (hỗ trợ cả click chuột và phím `R`).

2. **Hệ thống Âm thanh Tự sinh (Procedural Web Audio API):**
   - Không cần tải bất kỳ tệp âm thanh bên ngoài nào (0 KB asset, chuẩn MIT/CC0, giải quyết triệt để vấn đề mạng chậm hoặc thiếu file).
   - Âm thanh được tổng hợp thời gian thực từ các bộ dao động tần số (`OscillatorNode` & `GainNode`): Tiếng quẫy nước bắt cá, tiếng thu hoạch rau trong trẻo, tiếng chuông cập bến / chuông bếp keng keng, tiếng leng keng khi khách thanh toán tiền, và còi cảnh báo ngạt nước.
   - Hỗ trợ nút bật/tắt âm thanh trực tiếp trên giao diện hoặc phím tắt `M`.

3. **Hiệu ứng đồ họa sống động (VFX Particle Engine):**
   - Hệ thống bọt khí oxy sủi tăm khi Út Sen lặn sâu dưới lòng sông.
   - Làn khói bếp mờ ảo bốc lên khi bếp ở trạng thái đang nấu (`cooking`).
   - Gợn sóng nước nhấp nhô nhẹ dọc theo đường chân trời mặt nước.

> **Cam kết tính tất định:** Toàn bộ tính năng sáng tạo trên được đóng gói 100% trong client giao diện web (`chonoi/web/index.html`), **hoàn toàn tắt ở chế độ headless**, không can thiệp hay làm thay đổi bất kỳ byte dữ liệu nào của simulation core và hợp đồng Test Contract v1.0.
```
