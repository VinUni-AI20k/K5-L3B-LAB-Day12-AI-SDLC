# Kế hoạch Phase 1 (PRD-0) — 60 phút

- **Mục tiêu:** chơi được **cả hai buổi** đúng phạm vi lõi PRD §2; smoke hai tiến trình qua file kho; tag `phase-1`.
- **Đặc tả chi tiết:** `docs/plan/phase-1-conformance.md` (đối chiếu PRD ↔ starter, payload 17 event, 13 test bắt buộc).

## Việc / người / phụ thuộc

| Lát (PRD §6.2) | Người | File | Phụ thuộc |
|---|---|---|---|
| 1 — bơi, oxy, chặn biên, giỏ | Cao Minh | `chonoi/sim/gather.py` | — |
| 2 — hái, bắt cá, cập bến, ghi kho | Nhật Minh | `chonoi/sim/gather_actions.py` | cần `step()` của lát 1 gọi helper |
| 3 — khách, giữ chỗ, kiên nhẫn | Văn Minh | `chonoi/sim/quan_customers.py` | cần `QuanSim.step()` mới |
| 4 — bếp, bưng, phục vụ, tiền | Đức Minh | `chonoi/sim/quan_service.py` | cần `QuanSim.step()` mới |
| HUD cả hai buổi | Vinh | `chonoi/web/index.html` | đọc snapshot, không chờ ai |
| Hợp đồng kho + sự kiện | Cao Minh | `docs/contracts/README.md` | chốt trước 0:15 |
| Test + ma trận + bằng chứng | Văn Minh | `tests/`, `docs/verification/` | chạy song song, đỏ trước xanh sau |
| TEAM/contract/skill/tag | Đức Minh | `TEAM.md`, `game.contract.json`, `.agents/skills/` | — |

## Quy ước chống conflict

- **Chỉ Cao Minh sửa `GatherSim.step()`**, **chỉ Văn Minh sửa `QuanSim.step()`**; người khác viết helper được gọi từ đó.
- `game.contract.json` chỉ Integrator sửa (chỉ `team`, `team_size`).
- Không ai sửa `tests/test_smoke_p1.py`.

## Mốc

| Phút | Việc |
|---|---|
| 0–15 | TEAM.md, `team_size=5`, hợp đồng kho/sự kiện, tạo nhánh, đọc PRD |
| 15–45 | 4 lát song song; phút 20 rà lát vướng; phút 25 xuất thử file kho thật |
| 45–55 | smoke 2 tiến trình trên `main`, ma trận truy vết, merge PR |
| 55–60 | tag `phase-1`, ghi trung thực cái chưa xong |

## Rủi ro

| Rủi ro | Xử lý |
|---|---|
| Hai người cùng sửa `step()` | đã chốt quy ước trên; PR review bắt buộc |
| `zero_oxy_ticks` lệch 1 tick | PRD: đếm **cả** tick oxy chạm 0 ⇒ `choke` ở 1859, `faint` 1979 |
| Bắt cá còn giữ đàn | PRD: **xóa đàn**, `fish_caught` mang `yield` |
| `faint` không xóa giỏ | PRD: bỏ giỏ LIFO, `lost` là mảng kind, kho rỗng |
| Quán chọn sai đối tượng interact | chọn theo (khoảng cách, bếp trước bàn, id); không tương tác được thì **bỏ lượt** |
