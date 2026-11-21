# Credits
Liệt kê asset ngoài (nguồn, giấy phép CC0/CC-BY/MIT) và công cụ AI đã dùng.

## Asset
**Không dùng asset ngoài.** Toàn bộ đồ họa và âm thanh do nhóm tự tạo bằng code, nên không có nguồn bên thứ ba hay giấy phép riêng. Nhân vật, bối cảnh, tên gọi là bản gốc của lab.

| Asset | Nguồn / cách tạo | Giấy phép |
|---|---|---|
| 21 hình SVG trong `chonoi/web/assets/` (Út Sen, cá linh / lóc / kèo, Cá Sấu Năm Chèo, bông điên điển / súng, kèo nèo, bến, bếp, bàn, khách, 6 món, 3 biểu tượng cảnh báo) | Vẽ bằng code, sinh bởi `tools/gen_assets.py` (chạy lại được, có test so khớp) | Tự tạo, cùng giấy phép với repo |
| Giao diện mode `day` "Sạp đêm chợ nổi" (Shop, màn chuyển pha, tạm dừng, tổng kết; sprite pixel đồng xu, bình oxy, áo phao, đèn lồng, sao) | Vẽ bằng code trong `chonoi/web/day.js` (lưới pixel + canvas), không có file ảnh | Tự tạo, cùng giấy phép với repo |
| 24 hiệu ứng âm thanh | Tổng hợp bằng Web Audio trong `chonoi/web/assets/sfx.js` (dao động + nhiễu), không có file âm thanh | Tự tạo, cùng giấy phép với repo |

## Công cụ AI
- Claude Code (Anthropic): hỗ trợ viết `tools/gen_assets.py`, `sfx.js`, nối vào HUD và viết test. Người của nhóm kiểm lại bằng cách xem hình trong trình duyệt và chạy test. Chi tiết từng lần dùng: `docs/ai-usage-log.md`.
