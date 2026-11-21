# Credits
Liệt kê asset ngoài (nguồn, giấy phép CC0/CC-BY/MIT) và công cụ AI đã dùng.

## Tài nguyên Đồ họa & Giao diện (`chonoi/web/`)
- `chonoi/web/assets/gather_bg.png`: Hình nền pixel-art bầu trời và đáy nước buổi sáng (`mode: gather`), phục vụ qua `chonoi.live` (`/assets/gather_bg.png`).
- `chonoi/web/assets/menu_bg.png`, `quan_bg.png`, `shop_bg.png`: Hình nền pixel-art cho Menu chính, Quán nhà bè Má Tư buổi tối và Cửa hàng nâng cấp cuối ngày, tạo bằng AI image generator (Antigravity) cho dự án.
- `chonoi/web/assets/ut_sen.png`, `fish_ca_linh.png`, `fish_ca_loc.png`, `node_bong_dien_dien.png`, `node_bong_sung.png`: Sprites nhân vật Út Sen, đàn cá và bụi bông phục vụ qua `/assets/`.
- Đồ họa Canvas 2D nhà bè Má Tư, đèn dây vàng, khói bếp, Út Sen (áo bà ba, khăn rằn, kính lặn), đàn cá linh/cá lóc, bông điên điển/bông súng: Tự thiết kế bằng HTML5 Canvas 2D API trong `chonoi/web/index.html` (MIT License).

## Công cụ AI đã sử dụng
- **Antigravity (Gemini)**: Hỗ trợ thiết kế hợp đồng tích hợp, sinh unit/integration test, kiểm chứng tính tất định (`headless`), xây dựng HUD `chonoi.live` và hệ thống AI Harness (`AGENTS.md`, `.agents/skills/`).
