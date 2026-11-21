# Kiểm chứng Phase 2

| Yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Cá, hái và Cá Sấu | Regression các test gather, cá và Cá Sấu | `docs/proof/phase-2/fish-movement.md`, `fish-spawn.md`, `crocodile.md` | Đạt trên test hiện có |
| Kho 6 nguyên liệu | Hai tiến trình gather → kho → quan, gồm cá kèo và kèo nèo | `docs/proof/phase-2/integration.md` và các file `integration-*` | Đạt smoke |
| Vòng ngày, Shop, pause | Test hộp đen, 5 ngày với fixture rút ngắn, một ngày 22.200 tick | `tests/test_phase2_headless.py`, `docs/proof/phase-2/day-smoke.jsonl` | Đạt trên test hiện có |
| Giao diện chơi | Kiểm tra cú pháp JS, test LiveGame và chơi thử thủ công | `docs/proof/phase-2/integration.md` | Dùng xác nhận chơi thử OK |