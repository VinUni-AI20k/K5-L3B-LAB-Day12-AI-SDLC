# Proof QA Phase 2 — Nguyễn Minh Thành

Ngày: 21/11/2026

## Lệnh đã chạy

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 tools/verify_chur04_phase2.py
python3 .agents/skills/check-contract/check_contract.py
```

## Kết quả thực tế

- Unit/regression: 111/111 PASS.
- Smoke và verification: PASS; 111 test trong script.
- Determinism `day`: hai run giống byte; SHA-256 `56b42d48b76d961fd6b2b526300ef3840e082c16fd87ea73f630e880db9cae4f`.
- Full-day: 22.200 tick, kết thúc `days_complete`, `0.422347 s`.
- Inventory gather → quan: khớp.
- Contract check: `gather` và `quan` PASS.

## Diện tích đã kiểm

Regression P1, fixture P2, day/Shop/pause, buy theo frame, 2 bếp/4 bàn/6 món theo fixture, determinism và tích hợp kho.

## Giới hạn

Proof backend dùng `random_fish=false`, không chạy engine cá/quái mới và không thay manifest/UI. Không khẳng định DoD toàn nhóm hoặc tag `phase-2` đã đạt.
