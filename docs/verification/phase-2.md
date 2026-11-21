# Kiểm chứng Phase 2

| Phạm vi | Bằng chứng | Trạng thái |
|---|---|---|
| Q3 lịch, bốn bàn, menu/filter, reservation | [Q3 proof](../proof/phase-2/q3/README.md); `tests/test_p2_q3.py`, `tests/test_p2_quoc.py` | 10 test đạt trên tuning giả lập; chưa nghiệm thu v1.1 |
| Q3/Q4 hai bếp và Q4-F1 | `tests/test_p2_q3.py` | Code hiện tại không tiêu thụ reservation hai lần; Q4-F1 tái hiện, chờ chủ Q4 quyết định |
| Regression P1 | [Log](../proof/phase-2/q3/regression-headless.txt) | 98 test và 9/9 bước đạt, exit 0 |
| Day và contract v1.1 | Chưa có DaySim/contract v1.1 | Chưa chạy; chờ integrator |
| Rà soát Q4 5dbdf13 | [Patch và log đề xuất](../proof/phase-2/q3/q4-5dbdf13-proposed-tests.txt) | Trước patch 2/17 test lỗi; sau patch 19/19 đạt trong worktree tách biệt; Q4-F1 vẫn tái hiện, chưa ghép |
| Kiểm lại Q3 | [Regression hiện tại](../proof/phase-2/q3/current-verification.txt), `current-p2-tests.txt`, `current-p1-q3-tests.txt` | 100 test, 9/9 bước; Q3 P2 12 test, Q3 P1 23 test, exit 0 |
