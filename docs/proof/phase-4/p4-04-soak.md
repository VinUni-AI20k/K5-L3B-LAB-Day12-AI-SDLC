# P4-04 · Soak headless 10 Ngày (AC-P4-03)

Chạy ngày 2026-11-21 trên Windows (Python 3.13), `game.contract.json` 1.2, từ gốc repo:

```bash
python3 -m chonoi.soak --seed 7 --days 10 --out docs/proof/phase-4/soak.json
```

Kết quả (`soak.json`): `days` 10, `days_completed` 10, `crashes` 0, `duration_s` khoảng 3,6 giây (thời gian thật, thay đổi theo máy), 10 dòng `results`.

- Chạy bằng chế độ `day` trong một tiến trình; Ngày 6–10 lặp lại kế hoạch D1–D5 (test kiểm `DaySim._plan_for(d) == _plan_for(d - 5)`).
- Cùng seed cho cùng `results` (test `test_same_seed_gives_identical_results`); chỉ `duration_s` thay đổi.
- Test: `tests/test_p4_soak.py` (9 test), phá thử 7 cách (không đếm crash, không ghi kết quả từng Ngày, crash vẫn thoát 0, không kiểm `--days`, bot hành động mọi pha, bot không bấm `interact`, `days` sai): cả 7 bị bắt.

## Giới hạn (nói thẳng)
- Bot chỉ lặn, hái nút và về bến; **không nấu, không phục vụ, không mua ở Shop**. Vì vậy tiền luôn 0 và uy tín về 0 từ Ngày 3. Soak kiểm độ bền qua nhiều Ngày (bàn giao kho cá thể, hao tươi, khách đến rồi đi, đổi Ngày, kế hoạch lặp), không kiểm kinh tế hay luồng nấu và phục vụ.
- Dạng `results[]` và bot là giả định (`docs/clarify.md` dòng P4-04), chờ đối chiếu Ticket-04.
- `bench_cmd` và `soak_cmd` chưa khai trong `game.contract.json` (việc P4-02, contract 1.3).
