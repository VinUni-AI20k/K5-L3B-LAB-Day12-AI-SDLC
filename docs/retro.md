# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt:
  - Có **nhánh nền** `mKhaiTruong/contract-v1.1` (PR #14 draft) ngay đầu phase. Cả nhóm tách nhánh từ đó, nên `main` luôn xanh dù contract v1.1 làm hỏng test cũ.
  - Checklist việc của từng người ghi thẳng trên PR #14, kèm hàm dùng chung (`plan_ingredients`, `check_reserved_within_stock`, `MonsterSet`).
  - Review có gộp thử trong worktree tạm + chạy toàn bộ test trước khi merge. Bắt được conflict `scenario.py` ở PR #15 và 3 điểm lệch PRD (thứ tự event tick 0, trường thừa trong snapshot, khách ngoài kế hoạch); Khánh sửa trong 1 commit.
- Điều tệ:
  - Khuê và Khánh **cùng viết** kiểm scenario `day`, vì Khánh tách nhánh trước khi commit scenario lên nhánh nền → mất thời gian và phải rebase.
  - Lát gather (cá bơi/sinh + nối Cá Sấu) là phần nặng nhất nhưng chỉ một người làm, thành điểm nghẽn cuối phase.
  - UI menu/HUD v1.1 chưa ai làm.
- 1 hành động cho Phase 3: **báo trong kênh nhóm trước khi bắt đầu một file dùng chung** (`scenario.py`, `runner.py`, `contract.py`) và push nhánh nền ngay sau mỗi commit, để không ai viết trùng. Người nhận: Khuê (Integrator).

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
