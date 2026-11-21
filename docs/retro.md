# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt: chốt sớm giao diện chuyển pha (`GatherSim(day, oxygen_max_s, hp_max)` → kho đếm trong bộ nhớ → `QuanSim(menu_filter, …)` → `ShopSim`) nên hai lát gather và day làm song song mà ghép không vỡ; pause làm một lần ở `runner.Session` dùng chung cho ba mode và cho `chonoi.live`; một Ngày headless chạy 0.76 s (giới hạn 20 s).
- Điều tệ / bị kẹt: 4 test P1 vỡ vì số chuẩn (4 bàn, 8 đàn, nút `attack` hợp lệ, `--mode day`) phải sửa kèm lý do; ticket mơ hồ ở nhiều chỗ (mẫu scenario mỗi Ngày, resume có nhận cạnh không, event tick 0 trước/sau snapshot) → 21 giả định trong `docs/clarify.md` chưa được PO xác nhận; phần UI (menu, DayIntro, HUD, pause menu) chưa làm.
- 1 hành động cho Phase 3: **Duyet (PO)** mang C-P2-B02, C-P2-B04, C-P2-B05 hỏi giảng viên đầu Phase 3 và cập nhật test nếu câu trả lời khác giả định.

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:

## Retro Phase 3 (đổi kho)
- Tốt: helper độ tươi đơn vị nguyên (240/điểm) chốt sớm ở `inventory.py` → gather và quán dùng chung, ngưỡng 30/floor chính xác.
- Tốt: lớp chuyển fixture giữ được regression P1–P2 mà không viết lại hàng loạt test.
- Cần cải thiện: hai lát cùng sửa test smoke P1 song song; lần sau chốt người sở hữu từng file test trước khi chia việc.
