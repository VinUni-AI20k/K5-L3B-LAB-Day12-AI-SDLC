# Kiểm chứng Phase 4 — phần Soak của Quoosc

| AC | Bằng chứng | Kết quả |
|---|---|---|
| AC-P4-03 CLI/test | `python -m unittest tests.test_p4_soak -v` | đạt; chạy real DaySim qua Session; test ngày đơn, 10 ngày, replay, input lỗi, runtime crash, output lỗi |
| AC-P4-03 soak thật 10 ngày | [`soak-run.txt`](../proof/phase-4/soak-run.txt), [`soak.json`](../proof/phase-4/soak.json), [`soak-replay.json`](../proof/phase-4/soak-replay.json) | 10/10 ngày, 0 crash, exit 0; gameplay fields trùng hai lần seed 7 |
| Tích hợp full Phase 4 | Phase 4 plan/QA matrix | chưa nghiệm thu toàn nhóm: bench, cảnh báo UI, package/release và review QA thuộc teammate |

Kết quả per-day trong lần chạy thật: `earned=0`, reputation 3.0, score 300 cho cả 10 ngày. Bot kết thúc Gather ngay tại bến theo thiết kế, để Quan chạy tự nhiên và không tạo giao dịch. Đây là số liệu thật của chiến lược bot đã định, không phải kết quả economy.
