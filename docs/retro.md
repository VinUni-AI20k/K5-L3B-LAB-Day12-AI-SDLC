# Retro nhóm

## Phase 2 (nhanh)
> Nháp do Integrator soạn từ lịch sử repo; cả nhóm bổ sung trong 5 phút retro.
- Điều tốt:
  - Chốt contract v1.1 + hợp đồng mục 5 trước khi các lát bắt đầu → 4 lát P2 làm song song, mỗi PR gộp riêng đều xanh.
  - Hai lát tự chuyển phần lọc vào sim của mình (`QuanSim(menu_filter)`, `GatherSim(day)`) thay vì sửa chồng trong `day.py`.
  - Skill `kiem-tat-dinh` / `smoke-hai-tien-trinh` chạy lại được ngay cho `day`; bằng chứng P2 sinh trong vài phút.
- Điều tệ:
  - Tag `phase-1` trễ hạn; lát 4 P1 (PR #2) phải sửa 2 vòng và có lúc sửa test của lát khác để test xanh khi luật sai.
  - 4 PR dồn vào cuối phase → xung đột `day.py`, `index.html`, `ai-usage-log.md`, `standup.md`.
  - Chưa ai làm UI vòng ngày (AC-P2-45) và chưa chơi thử HUD lưu ảnh; chưa có mục Mở rộng.
- 1 hành động cho Phase 3: mỗi lát mở PR nháp ngay khi có commit đầu và chạy toàn bộ test trước khi xin review; **không sửa test của lát khác** nếu không ghi lý do trong commit. Người nhận: nglngnguyen-gh (Integrator) nhắc ở standup phút 20.

## Phase 3 (nhanh — đổi kho đếm → kho cá thể)
> Nháp do Integrator soạn từ lịch sử repo; cả nhóm bổ sung.
- Điều tốt:
  - Ghi tác động + quyết định schema trước (`docs/plan/phase-3.md`), adapter `items.py` lên `main` khi manifest vẫn v1.1 → `main` luôn xanh trong lúc chuyển.
  - Biểu diễn độ tươi bằng số nguyên đơn vị (240/điểm) → không lệch ở ngưỡng 30 và phép floor giá.
  - Test v1.2 của `day` viết trước, tự bật khi manifest lên 1.2 → lúc bật đã có kiểm tích hợp.
- Điều tệ:
  - Bật v1.2 làm vỡ ~67 test P1–P2 vì fixture / kỳ vọng ghi cứng kho đếm; mất nhiều thời gian chuyển test (lý do ghi trong commit).
  - Lát gather v1.2 không có commit tới phút ~25 → Integrator làm thay; PR #11 làm trùng phần đã có trong PR #9.
  - Mở rộng (burn) vẫn chưa gộp.
- Rút ra từ lần đổi kho: test nên đọc dữ liệu qua helper (`hold_items`, `counts_of`) thay vì ghi cứng schema.
- 1 hành động cho Phase 4: phút 10 mỗi người báo commit đầu trong kênh; lát không có commit thì Integrator chia lại ngay. Người nhận: nglngnguyen-gh.

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
