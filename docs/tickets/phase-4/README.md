# Tickets — Phase 4 (contract v1.3, phát hành v1.0.0)

Spec: `docs/specs/phase-4.md`. **Điều kiện vào: `phase-2` + `phase-3` đã tag.**

| # | Ticket | Blocked by | Người | Vai (PRD §4) |
|---|---|---|---|---|
| 01 | `bench_cmd`: đo FPS thật, `bench.json` | P2-02, P3-01 | Văn Minh | Bench/QA |
| 02 | `soak_cmd`: 10 Ngày, `soak.json` tất định | P2-05 | Cao Minh | Bench/QA (pair) |
| 03 | Cảnh báo + chế độ tương phản cao | P2-06 | Vinh | Đóng gói (UI) |
| 04 | Đóng gói + Release `v1.0.0` + contract 1.3 | 01, 02, 03 | Đức Minh | Release/Integrator |
| 05 | Mở rộng: leaderboard cục bộ | 02 | Nhật Minh | — |
| 06 | Retro + ma trận AC-P4 + phản tư cá nhân | 01–04 | Đức Minh | Điều phối retro |

**Thứ tự:** 01 và 03 chạy song song ngay khi P2/P3 xong; 02 sau `day`; 04 gom tất cả; 05/06 cuối.

**Luật chung:** contract chỉ Đức Minh (Integrator) sửa ở 04; `tools/bench.py`/`tools/soak.py` của người làm 01/02;
`web/index.html` của Vinh; không đổi tuning/kho/JSONL (v1.2 giữ nguyên).
