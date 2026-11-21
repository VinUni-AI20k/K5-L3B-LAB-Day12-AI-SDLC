# Kế hoạch Phase 1 (≤ 1 trang)

> Nhóm AnhChang3Chan, 6 người. Số liệu và AC chi tiết sẽ bổ sung sau khi đọc PRD-0 trên lab board (chưa suy diễn).

## Mục tiêu
- Bản chơi được của gather (buổi sáng) và quan (buổi tối) theo PRD-0, có headless đúng Test Contract.
- Smoke test + test của nhóm xanh; bằng chứng thật trong `docs/proof/phase-1/`; gắn tag `phase-1` trước mốc 1:00.

## Việc / người / phụ thuộc
| Việc | Người (handle) | File chính | Phụ thuộc |
|---|---|---|---|
| Lát 1: bơi, oxy, ngạt, Máu, ngất, sự kiện dive/surface/oxygen_empty/choke/faint | An (`AnK17-UIT`) | `chonoi/sim/gather.py` (`_step_oxygen_and_hp`) | PRD-0 mục gather |
| Lát 2: hái nút, bắt cá, giỏ LIFO, cập bến, kho | Bảo (`thbao4545`) | `chonoi/sim/gather.py` (`_try_harvest_node`, `_try_catch_fish`) | Lát 1 (trạng thái mặt nước/oxy) |
| Lát 3: khách, giữ chỗ, kiên nhẫn, bỏ đi, no_dish + kiểm scenario | Vũ (`hoangvu1806`) | `chonoi/sim/quan.py`, `chonoi/scenario.py` | PRD-0 mục quan |
| Lát 4: bếp, bưng, phục vụ, tiền, tip, uy tín | Hà Anh (`hnha02`) | `chonoi/sim/quan.py` (`_step_stoves_and_eating`, `_handle_interact`) | Lát 3 (vòng đời khách) |
| Godot: hiển thị, HUD, asset (chỉ đọc snapshot) | Gia Bảo (`Jay-Gabriel`) | `godot/`, `CREDITS.md` | Schema snapshot |
| QA/PO: hợp đồng, clarify, test, harness, proof, nhật ký AI | Nhật Nguyên (`double-n-021`) | `tests/`, `docs/`, `.agents/`, `AGENTS.md` | PRD-0 |

## Mốc nội bộ (60 phút)
- 0-15: đọc PRD-0 hai lần, chốt `docs/contracts/README.md`, `docs/clarify.md`, giao Lát.
- 15-45: code theo helper riêng, commit nhỏ, push thường xuyên.
- 45-55: chạy `headless-contract-check`, lưu proof, điền `docs/verification/phase-1.md`.
- 55-60: `phase-gate-audit`, Integrator gắn tag `phase-1`.

## Rủi ro
- Merge conflict ở `step()` của gather/quan: dùng helper riêng, pull trước khi sửa.
- Lát 2 phụ thuộc Lát 1, Lát 4 phụ thuộc Lát 3: thống nhất tên trường trạng thái sớm.
- Thiếu commit của một thành viên: kiểm bằng `git shortlog -sne` ở phút 45.
- Tên repo chưa đúng quy ước `K5-L3B-LAB-Day12-AI-SDLC-<ten-nhom>`: hỏi Coach trước khi nộp.
