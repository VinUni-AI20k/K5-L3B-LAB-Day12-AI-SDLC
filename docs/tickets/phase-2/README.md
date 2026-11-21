# Tickets — Phase 2 (contract v1.1)

Spec: `docs/specs/phase-2.md` · Nguồn: TICKET-02 / PRD `#phase-2`.
Điều kiện vào: `phase-1` đã tag trên `main` (v1.0 xanh). Đổi số sang v1.1 trước khi tag `phase-1` là sai hợp đồng.

| # | Ticket | Blocked by | Người | Lát PRD §5 |
|---|---|---|---|---|
| 01 | Contract v1.1 + schema/CLI/envelope (prefactor) | — (sau tag P1) | Cao Minh | mở đường |
| 02 | Cá bơi + sinh + 3 loài + số chuẩn | 01 | Nhật Minh | (1) |
| 03 | Cá Sấu + Máu/ngất + bất tử | 01 | Văn Minh | (2) |
| 04 | Quán 2 bếp / 4 bàn / 6 món / kế hoạch ngày | 01 | Đức Minh | (3) |
| 05 | `day` + Shop + pause | 01 (mềm: 02–04) | Cao Minh | (4) |
| 06 | Menu / intro / result / HUD / pause UI | 01 | Vinh | (4, phần UI) |
| 07 | Mở rộng **Vợt hút cá (net)** | 02, 05 | Nhật Minh | mở rộng |

**Luật chơi của phase:** mỗi người một nhánh `feat/<tên>`; PR đợt 1 lúc **1:20**, đợt 2 lúc **1:40**, đợt 3 lúc **1:50**; merge theo thứ tự 01 → 02 → 03 → 04 → 05 → 06; chạy `python3 tools/run_checks.py` sau mỗi đợt.

**Ai sửa file nào (chống conflict):**
- `chonoi/contract.py`, `chonoi/scenario.py`, `chonoi/headless.py`, `chonoi/runner.py` → **chỉ Cao Minh** (ticket 01).
- `chonoi/sim/gather.py` → Cao Minh (01) và Văn Minh (03) qua helper `monster_step`.
- `chonoi/sim/fish.py` (mới) → Nhật Minh.
- `chonoi/sim/quan*.py` → Đức Minh.
- `chonoi/sim/day.py` (mới) + `shop.py` → Cao Minh.
- `chonoi/web/index.html` → Vinh.
- `tests/` → người làm lát viết test của lát; Văn Minh giữ ma trận.
