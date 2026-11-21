# Bằng chứng Phase 2 Q3

Trên `3ce5cc6` cùng working tree Q3, Python 3.11 Windows, script verification dùng shim Python ngoài repo. `p2-tests.txt`: 10 test, exit 0; `p1-q3-tests.txt`: 23 test, exit 0; `regression-headless.txt`: 98 test, exit 0, 9/9 bước gồm hai lần headless gather/quán cùng seed so byte, nạp kho và đầu vào sai. Các test Phase 2 sử dụng [tuning giả lập](../../../../tests/fixtures/p2/q3/tuning.json), không phải contract chính thức.

Headless `quan` ở đây dùng contract v1.0. Chưa chạy được headless `day` hoặc headless bằng contract v1.1 chính thức do chưa có DaySim/v1.1. Hai bếp trên code hiện tại không dùng lại reservation; test Q4-F1 tái hiện món mồ côi, không biểu thị lỗi đã sửa. Nhánh Q4 `8b3b93f` cần tích hợp/retest thực tế; xem `specs/001-p2-q3-day-customers/contracts/q3-q4-day.md`.

Lệnh tái hiện: `python -m unittest tests.test_p2_q3 tests.test_p2_quoc -v`; `python -m unittest tests.test_p1_q3 -v`; `python .agents/skills/phase-1-verification/scripts/verify_phase1.py --no-proof`.
