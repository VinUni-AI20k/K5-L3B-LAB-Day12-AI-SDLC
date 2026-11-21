# Ma trận truy vết Phase 4

| AC | Nội dung | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P4-01 | Contract v1.3 và bench/soak commands | `tests.test_p4_contract` | `game.contract.json`, `tests/test_p4_contract.py` | Đạt; main `ff4b376` |
| AC-P4-02 | Benchmark 30 giây và UI contrast | Benchmark/CDP và unit tests | [`ui-client`](../proof/phase-4/ui-client/) | Bằng chứng hiện có; thuộc owners của bench/UI |
| AC-P4-03 | Soak 10 ngày, 0 crash, replay gameplay | Hai lần chạy thật `python -m chonoi.soak --seed 7 --days 10`; 75 focused tests | [`run 1`](../proof/phase-4/soak-q3-run1.json), [`run 2`](../proof/phase-4/soak-q3-run2.json), [`focused tests`](../proof/phase-4/q3-focused-tests.txt) | Kỹ thuật đạt: 10/10 ngày, 0 crash, gameplay fields giống nhau; QA/Integrator review còn chờ |
| AC-P4-04 | UI alerts và high contrast | CDP screenshots + unit tests | [`ui-client`](../proof/phase-4/ui-client/) | Bằng chứng hiện có; thuộc owners của UI |
| AC-P4-05 | Clean clone/package | Clean-clone log | [`clean-clone.txt`](../proof/phase-4/clean-clone.txt) | Theo log nhóm; không thuộc Q3 |
| AC-P4-06 | Regression P1–P3 | Full unittest + Phase 1 verifier | [`full regression`](../proof/phase-4/q3-full-regression.txt), [`Phase 1 verifier`](../proof/phase-1/verify-run.txt) | 212 tests OK; verifier 9/9 |
| AC-P4-07 | Release artifacts/tag | GitHub release/tag | external | Chưa xác nhận trong nhánh này |
| AC-P4-08 | Retrospective cá nhân/team | `docs/retro.md`, `docs/members/` | project docs | Phần tự phản tư cá nhân cần Quốc xác nhận; agent không tự ghi thay trải nghiệm cá nhân |

## Ghi chú soak của Quoosc

- Chạy hai lần production tuning với seed 7: cả hai `days_completed=10`, `crashes=0`, exit 0; trường `days`, `days_completed`, `crashes`, `results` khớp nhau.
- `earned=0` và `reputation=3.0` là kết quả thật của bot fast-dock không đi lấy nguyên liệu; proof không khẳng định cân bằng kinh tế hay chiến lược chơi tốt.
- Soak mở rộng day plan qua chu kỳ D1–D5; kiểm tra bằng `tests.test_p4_soak` với DaySim thật.
- Kết quả AC-P4-03 đã có bằng chứng kỹ thuật; chưa có phê duyệt QA/Integrator.
