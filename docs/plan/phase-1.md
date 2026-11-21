# Kế hoạch Phase 1 (≤ 1 trang)

- **Mục tiêu:** đến 1:00 gắn tag `phase-1` với gather + quán chạy đúng PRD-0, smoke test và test của nhóm đều xanh, có ma trận kiểm chứng trong `docs/verification/phase-1.md`. Giữ starter Python (chỉ thư viện chuẩn).

## Mốc thời gian
| Giờ | Việc |
|---|---|
| 0:00–0:15 | Kickoff: fork + collaborator, điền `TEAM.md` + `team_size`, chốt `docs/contracts/` (schema kho, sự kiện, giao diện sim ↔ UI), mỗi người tạo `docs/members/<handle>.md` |
| 0:15–0:35 | Code lát 1–4 song song; E viết test hộp đen theo AC của PRD-0 |
| 0:35 | Standup 5 phút (ghi `docs/standup.md`) |
| 0:35–0:50 | Hoàn thiện, merge, chạy test toàn bộ, chơi thử `chonoi.live` |
| 0:50–1:00 | Ghi bằng chứng, `docs/verification/phase-1.md`, Integrator gắn tag `phase-1` |

## Việc / người / phụ thuộc
| Lát | Người | File | Nội dung | Phụ thuộc |
|---|---|---|---|---|
| 1 | A (Integrator) | `chonoi/sim/gather.py` | dive/surface, oxy theo `d` cuối bước, `oxygen_empty`, ngạt → `choke`, Máu 0 → `faint` + `gather_end("fainted")` giỏ rỗng; giỏ LIFO | contracts (sự kiện) |
| 2 | B | `chonoi/sim/gather.py` | hái nút `ready` gần nhất trong `interact_radius` (id nhỏ khi bằng nhau) ở mặt nước, `gather`/`hold_full`, `regrow_ticks`; `catch` dưới nước khi hết cooldown, `fish_caught`/`hold_full`, `fish_yield` | lát 1 (giỏ) — thống nhất hàm thêm vào giỏ trước |
| 3 | C (PO) | `chonoi/sim/quan.py` | khách theo lịch (`first_customer_tick`, `customer_interval_s`), chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn, `customer_left`, `no_dish` | schema kho |
| 4 | D | `chonoi/sim/quan.py`, `chonoi/scenario.py` | một `interact`/tick theo (khoảng cách, bếp trước bàn, id): `cook_started`, `dish_ready`, `dish_picked`, `served`, `paid`, boa, uy tín, `quan_end`; kiểm mâu thuẫn scenario quán → mã 2 | lát 3 (khách, giữ chỗ) |
| QA/UI | E (QA lead) | `tests/test_gather_p1.py`, `tests/test_quan_p1.py`, `chonoi/web/index.html`, `.agents/skills/` | mỗi AC ≥ 1 test hộp đen (dùng `tests/helpers.py`), HUD, 2 skill nhóm | AC trong PRD-0 |

**Quy ước:** số liệu chỉ đọc từ `game.contract.json`; ngẫu nhiên chỉ qua `Streams`; sắp bằng `sort_by_id`; không sửa khung giảng viên; nhánh `feat/<lát>` → PR nhỏ, test xanh mới merge; mỗi người ≥ 3 commit có nội dung.

## Rủi ro
- **PRD-0 mơ hồ** (ví dụ `fish_yield` vượt chỗ trống thì `hold_full` hay nhặt một phần) → PO ghi `docs/clarify.md`, hỏi ngay, không tự bịa.
- **Lát 1 và 2 cùng sửa `gather.py`** → chia rõ vùng code (lát 1: bước oxy; lát 2: nhánh `interact`/`catch`), merge sớm, tránh xung đột.
- **Lát 4 chờ lát 3** → chốt trước cấu trúc `customer` (trường, trạng thái) trong `docs/contracts/`.
- **Mất tính tất định** (dùng `random`/đồng hồ, duyệt dict không sắp) → chạy headless 2 lần, so byte trước khi merge.
- **Trễ giờ** → hết 0:55 thì gắn tag với phần đã xanh, ghi trung thực phần chưa đạt.

## Kiểm chứng trước khi gắn tag
- `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` xanh.
- `python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out a.jsonl` chạy 2 lần, giống từng byte.
- gather `--inventory-out kho.json` → quan `--inventory kho.json`: `stock` khớp.
- `python3 tools/check_team.py` OK.
