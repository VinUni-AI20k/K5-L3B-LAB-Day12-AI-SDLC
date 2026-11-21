# Kế hoạch Phase 1 (≤ 1 trang)

- **Mục tiêu:** `gather` (oxy, ngạt, Máu, ngất, hái, bắt cá, giỏ, ghi kho) và `quan` (khách, giữ chỗ, bếp, phục vụ, tiền, uy tín) đúng PRD-0. Test xanh, gắn tag `phase-1` trước 1:00.

## Nguyên tắc chống block
1. **Một file hoặc một hàm, một chủ.** Lúc 0:10, Integrator đẩy commit khung: tách `step()` thành các hàm rỗng (no-op, test vẫn xanh). Mỗi người chỉ viết thân hàm của mình, không ai sửa chung một khối code.
2. **Chốt hợp đồng trước khi code** (`docs/contracts/README.md`, trước 0:15): các trường của khách và bếp, tên và `data` của sự kiện, schema kho.
3. **Test bằng scenario, không chờ người khác.** Lát 4 dựng sẵn khách trong `scenario.customers`. Lát 2 test hái ở mặt nước, không cần oxy. `quan` dùng `scenario.stock` hoặc `docs/contracts/inventory.sample.json`, không chờ `gather`.
4. **Mỗi người một file test riêng:** `tests/test_p1_<lát>.py`.

## Việc / người / phụ thuộc
| Lát | Người | File / hàm sở hữu | Phụ thuộc |
|---|---|---|---|
| Khung + hợp đồng | invzble-z | `docs/contracts/`, commit khung `step()`, `game.contract.json` | Không (làm đầu tiên, 0:00–0:15) |
| G1 oxy, ngạt, Máu, ngất | comtrang378-ship-it | `gather.py`: `_update_oxygen()`, dive/surface/choke/faint | Commit khung |
| G2 hái, bắt cá, giỏ | NguyenQuangDunghe161764 | `gather.py`: `_try_harvest()`, `_try_catch()`, `_push_hold()` | Commit khung |
| Q3 khách, giữ chỗ, kiên nhẫn | Quoosc | `quan.py`: `_spawn_customers()`, `_tick_customers()`, dựng khách từ scenario | Hợp đồng khách |
| Q4 bếp, bưng, phục vụ, tiền | ttkien0710 | `quan.py`: `_tick_stoves()`, `_interact()`, paid/tip/uy tín | Hợp đồng khách (không chờ Q3) |
| QA | WorkOfMinh | `tests/test_p1_contract.py`, `scenario.py` (mâu thuẫn → mã 2), `docs/verification/phase-1.md`, `docs/proof/phase-1/` | AC từ PRD-0 |
| PO + harness | nganhduong123 | `docs/clarify.md`, plan, standup, `ai-usage-log.md`, 2 skill trong `.agents/skills/`, `AGENTS.md` | Không |

## Mốc giờ
- 0:00–0:15: cả nhóm đọc PRD-0; PO gom câu hỏi; Integrator chốt hợp đồng và đẩy commit khung.
- 0:15–0:45: làm song song theo lát, mỗi lát một PR nhỏ; người dự phòng review.
- 0:30: standup 3 phút.
- 0:45–0:55: Integrator gộp; QA chạy toàn bộ test và headless, điền verification và proof.
- 0:55: gắn tag `phase-1` (chỗ chưa xong ghi trung thực).

## Rủi ro
- Sửa chung `gather.py`/`quan.py` gây xung đột: chỉ viết trong hàm của mình, rebase lên `main` trước khi mở PR.
- Đề cho 4–6 người, nhóm có 7 người (xem `docs/clarify.md` #1).
