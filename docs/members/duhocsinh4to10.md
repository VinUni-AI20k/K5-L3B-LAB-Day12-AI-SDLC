# duhocsinh4to10 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm:** Phụ trách `client/ui` và Demo Lead qua Phase 1–2: nâng cấp [`chonoi/live.py`](../../chonoi/live.py) (`--mode day`, Shop, Pause dừng mọi timer, xuất `menu`/`day_plan` động) và [`chonoi/web/index.html`](../../chonoi/web/index.html) (6 màn hình Menu/DayIntro/EveningIntro/DayResult/Shop/Summary, HUD v1.1 `≥18px` @ `1280×720`, cảnh báo Thủy quái viền tím & Hết hơi, vẽ Cá Sấu Năm Chèo, 2 bếp/4 bàn, kho khả dụng, tương thích sprite atlas & `ut-sen-swim.png`), viết [`tests/test_ui_live.py`](../../tests/test_ui_live.py) cùng bằng chứng Phase 1–2. *(Commit chính: `0e3839f`, `0b8f3ad`.)*
- **Tôi đã review:** Đọc diff `f200323`, `7a5d7df`, `351535b`, `4672dc8` và `2ae7f6e` (`quan_customers.py`, skills) để tích hợp không mất code đồng đội.
- **AI sai ở đâu và tôi phát hiện thế nào:** Lúc đầu dễ hard-code thực đơn 3 món ở client; phát hiện khi đối chiếu `quan_customers.py` và `phase-2.md`, nên chuyển sang đọc động `snap.menu` và `available_stock` từ `tuning`.
- **Điều tôi học được:** Giữ UI hoàn toàn hướng dữ liệu từ snapshot giúp phát triển song song với lõi v1.1 mà không phá Test Contract headless.
