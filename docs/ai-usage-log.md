# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | TV1 (Nguyễn Duy Mạnh) | Antigravity (Gemini 4 Hydrogen) | Triển khai sinh tồn ca sáng trong `chonoi/sim/gather.py`, viết 3 test headless `tests/test_gather_survival.py`, điền `docs/standup.md`, `docs/verification/phase-1.md` | Chưa đo | Tự đối chiếu thứ tự bước mục F và điều kiện biên `zero_oxy_ticks` (bước chạm oxy 0 tính là bước ngạt đầu tiên); chạy `tests/test_gather_survival.py` đạt 3/3. |
| 1 | TV2 | Antigravity (Gemini 4 Hydrogen) | Triển khai hái nút, bắt cá, cooldown, hòa ID trong `chonoi/sim/gather.py` và bộ test `tests/test_gather_harvest.py` | - | Tự động chạy kiểm chứng 9/9 test biên và smoke 2 tiến trình Mục G đều đạt. |
| 1 | TV4 | Codex | Đối chiếu mục D–F, triển khai bếp và thanh toán, viết và chạy test headless | Chưa đo | Xem [kết quả TV4](proof/phase-1/tv4-bep-thanh-toan.md). |
| 1 | TV5 (Vũ Xuân Bách) | Gemini 3.8 Flash | Soạn thảo ma trận kiểm chứng `phase-1.md`, viết `test_phase1_gameplay.py`, tích hợp 3 tính năng sáng tạo Web Audio & Canvas UI | ~18.000 tokens | AI viết kịch bản test giữ nguyên phím `interact=True` khiến không phát hiện được cạnh lên ở thao tác tiếp theo; phát hiện khi chạy unittest fail và sửa nhả phím `interact=False` |

| 2 | TV1 (Nguyễn Duy Mạnh) | Codex (GPT-6.1) | Viết logic Cá Sấu, fixture/snapshot, tuning, test và tài liệu kiểm chứng | Chưa đo | Kiểm tra off-by-one của recoil/bất tử bằng snapshot từng tick, đối chiếu lost của monster_hit và faint để tránh bỏ giỏ hai lần sai thứ tự. Suite đạt 70/70. |
| 2 | TV2 | Antigravity (Gemini 4 Hydrogen) | Cập nhật 6 nguyên liệu, N5/N6, 8 đàn cá ban đầu, cá bơi/phản xạ/đổi hướng/sinh theo lịch (`chonoi/sim/gather.py`, `inventory.py`, `scenario.py`, `contract.py`, `game.contract.json`) và `tests/test_gather_fish_p2.py` | - | Toàn bộ 49 test (gồm P2 cá & regression P1) đạt; cập nhật `test_smoke_p1.py` (`len(fish) == 8`) và `test_gather_harvest.py` (`random_fish=False`) theo v1.1. |
