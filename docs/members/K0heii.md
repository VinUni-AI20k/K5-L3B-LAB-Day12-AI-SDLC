# K0heii — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - Đợt 1 (`M6.1`–`M6.2`, commit `cab9595`): điền đủ 6 thành viên & thỏa thuận nhóm trong `TEAM.md`, cập nhật `team_size: 6` trong `game.contract.json`, khóa hợp đồng tích hợp (`docs/contracts/README.md`), lập kế hoạch `docs/plan/phase-1.md` và chốt câu hỏi PRD-0 trong `docs/clarify.md`.
  - Đợt 2 (`M6.3`): bổ sung kiểm tra mâu thuẫn mức luật cho scenario quán trong `chonoi/scenario.py`, nối kiểm kho `--inventory` trong `chonoi/headless.py` và viết bộ unit test `tests/test_scenario_m6.py`.
  - Chuẩn bị Đợt 4: bổ sung DoD cho `README.md`, dựng ma trận truy vết `docs/verification/phase-1.md` và test tích hợp/tất định `tests/test_integration_m6.py`.
- **Tôi đã review (kèm link):** *(Cập nhật sau vòng review chéo M5 ↔ M6 ở Đợt 4)*
- **AI sai ở đâu và tôi phát hiện thế nào:** Lúc đầu chưa có `PRD0.md`, AI giả định `hand` là chuỗi mã món; sau khi đối chiếu PRD-0 mục D phát hiện `hand` và `stoves[].dish` là object `{order_id, dish_id, base_price}` nên đã sửa lại hợp đồng và rule validate.
- **Điều tôi học được:** Chốt rõ hợp đồng dữ liệu và tách việc kiểm mâu thuẫn `scenario.py` sớm giúp các module còn lại làm song song mà không lệch schema khi ghép.
