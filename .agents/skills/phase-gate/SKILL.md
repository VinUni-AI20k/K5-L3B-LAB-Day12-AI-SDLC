---
name: phase-gate
description: Chạy cổng kiểm trước khi gắn tag phase-n của lab Day 12. Dùng khi sắp tag, khi nghi main đỏ, hoặc khi cần biết "đã đủ điều kiện bàn giao chưa".
---

# Phase gate

Một lệnh, ba cổng, một quyết định: **tag được hay chưa**.

## Chạy

```bash
python3 tools/run_checks.py        # unittest + smoke hai tiến trình + tất định
```

Kết quả ghi vào `docs/proof/phase-1/checks-latest.md`. Mã thoát 0 = đủ điều kiện.

## Checklist trước khi tag

1. `git status` sạch; đang ở đúng commit bàn giao trên `main`.
2. `python3 tools/run_checks.py` → **PASS** (in ra cả 3 cổng).
3. `python3 tools/check_team.py` → `OK: 5 thành viên`.
4. `docs/verification/phase-n.md` đã cập nhật **kết quả thật**, kể cả phần chưa đạt.
5. `docs/standup.md`, `docs/ai-usage-log.md` có dòng của phase này.
6. Tag trỏ đúng commit: `git tag -a phase-n -m "..." && git push origin phase-n`.

## Khi đỏ

- Đọc cổng nào đỏ trước — đừng sửa test cho xanh.
- Test đỏ vì luật chưa có → xem `docs/tickets/phase-n/` xem ai giữ lát đó.
- Test đỏ vì kỳ vọng sai → sửa test **và ghi lý do trong commit**.
- Không bao giờ tag khi `run_checks.py` đỏ: hidden test chấm đúng trạng thái tại tag.

## Tiến độ nhóm

```bash
python3 tools/team_progress.py     # commit từng nhánh + trạng thái merge
```
