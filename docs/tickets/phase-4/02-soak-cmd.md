# 02: `soak_cmd` — 10 Ngày headless, `soak.json`

**What to build:** Một lệnh chạy 10 Ngày liên tiếp trong một tiến trình headless bằng bot tất định, đi qua đủ `gather → quan → shop` mỗi Ngày, và ghi `soak.json` để chứng minh game không vỡ khi chơi dài.

**Blocked by:** P2-05 (`day` + Shop)

**Status:** ready-for-agent

- [ ] `<soak_cmd> --seed 7 --days 10 --out soak.json` chạy được; kế hoạch D1–D5 lặp lại ở Ngày 6–10.
- [ ] Mỗi Ngày qua đủ ba pha; tiền, `earned`, uy tín, cấp nâng cấp và id cá thể tiếp tục xuyên suốt.
- [ ] `soak.json` có `days, days_completed, crashes, results, duration_s`; mỗi `results[]` có `day, earned, reputation, score` tại lúc Shop đóng.
- [ ] Bot tất định: cùng seed + cùng `--days` → `results` giống nhau; so sánh **bỏ** `duration_s`.
- [ ] `crashes` đếm bằng try/except quanh từng bước; lỗi không làm mất file output (ghi phần đã chạy).
- [ ] Chạy 10 Ngày trên máy chấm ≤ 20 s/Ngày (ghi số đo thật vào proof); `days_completed == days` và `crashes == 0` mới coi là đạt.
- [ ] Artifact + log lưu `docs/proof/phase-4/`; kết quả ghi vào `docs/verification/phase-4.md`.
