# Ma trận kiểm chứng Phase 4

Kiểm chứng ngày 2026-11-21 trên code ở `main` `80c8ff4` (sau PR #15) và QA branch `7d9b946`. Đây chưa phải commit bàn giao cuối Phase 4; nếu code thay đổi trước khi phát hành, chạy lại bench, soak, regression và smoke trên commit tích hợp.

| Hạng mục | Lệnh / bằng chứng | Kết quả |
|---|---|---|
| Bench, cảnh render 1280×720, seed 42, làm nóng 3 s và đo 30 s | `python3 -m chonoi.bench --seed 42 --duration 30 --out docs\proof\phase-4\bench.json`; [bench.json](../proof/phase-4/bench.json) | Đạt: 257.13 avg FPS, 132.41 FPS 1% low, 7,715 frames / 30.004 s, load 84 ms; các mốc ≥60 / ≥30 / ≤10,000 ms đều đạt. |
| Hợp đồng bench và render | `tests.test_bench` trong regression bên dưới | Đạt: kiểm tra đủ 5 trường, quan hệ frames/measured_s và header framebuffer 1280×720. |
| Soak 10 ngày | `python3 -m chonoi.soak --seed 7 --days 10 --out docs\proof\phase-4\soak.json`; [soak.json](../proof/phase-4/soak.json), [soak-check.md](../proof/phase-4/soak-check.md) | Đạt: 10/10 ngày, 0 crash; lượt lặp cùng seed cho kết quả gameplay giống nhau khi bỏ `duration_s`. |
| Regression P1–P3 | `$env:PYTHONPATH='tests;.'; $env:PYTHONIOENCODING='utf-8'; python -m unittest discover -s tests -v`; [regression.txt](../proof/phase-4/regression.txt) | Đạt: 127/127 test. |
| Smoke gather → quan hai tiến trình | `$env:PYTHONIOENCODING='utf-8'; python3 tools\smoke_proof.py --phase phase-4`; [smoke.md](../proof/phase-4/smoke.md) | Đạt: 7/7 kiểm tra, gồm kho giao nhận, độ tươi và tính tất định. |

## Phạm vi còn chờ

Đây là kết quả QA của lát bench/soak/regression/smoke; chưa xác nhận DoD toàn Phase 4. Các thay đổi cảnh báo/tương phản, đóng gói và mở rộng cần được kiểm tra trên commit bàn giao trước khi gắn tag hoặc phát hành.

## Ma trận AC trên commit bàn giao `9bb4150` (tag `phase-4`, Release v1.0.0)

Chạy lại sau PR #16 (gộp đóng gói + burn, leaderboard, cảnh báo + tương phản, QA) theo hành động retro P2. Bằng chứng: `docs/proof/phase-4/handoff/`. Phần QA ở trên (khoa-asta, `80c8ff4`) giữ nguyên làm lịch sử.

| AC | Kiểm chứng / bằng chứng | Kết quả |
|---|---|---|
| AC-P4-01 | Contract v1.3: `contract_version` 1.3, `bench_cmd`, `soak_cmd` ở gốc; `chonoi/contract.py` kiểm khi load | đạt |
| AC-P4-02 | Bench có render `python3 -m chonoi.bench --seed 42 --duration 30`: [bench.json](../proof/phase-4/handoff/bench.json) — **682.27 avg FPS, 1% low 295.4, 20 468 frames / 30.0 s, load 75 ms** (mốc ≥ 60 / ≥ 30 / ≤ 10 s đạt); `tests/test_bench.py` | đạt (render offscreen — xem giới hạn) |
| AC-P4-03 | Soak `--seed 7 --days 10`: [soak.json](../proof/phase-4/handoff/soak.json) — days_completed 10, crashes 0; chạy lại cùng seed giống nhau khi bỏ `duration_s` | đạt |
| AC-P4-04 | 3 cảnh báo (THỦY QUÁI Ở GẦN, OXY SẮP HẾT · LÊN MẶT NƯỚC, KHÁCH SẮP GIẬN · PHỤC VỤ SỚM) + chế độ tương phản cao trong `chonoi/web/index.html`; [hud.md](../proof/phase-4/handoff/hud.md) 67/67 | đạt (tự động); chơi thử 3 cảnh báo ở tương phản cao: chưa có ghi chép chơi tay |
| AC-P4-05 | Clone sạch từ GitHub ở `9bb4150` → `python -m chonoi.live --mode day --days 5` trả HTTP 200 (mode day, Ngày 1); README ghi môi trường, điều khiển, test, headless, bench, soak | đạt (kiểm trên Windows bằng `python`) |
| AC-P4-06 | Gói `dist/cho-noi-v1.0.0.zip` / `.tar.gz` (`tools/package_release.py`, 29 file): giải nén chạy được headless day, bench, live (HTTP 200); CHANGELOG theo phase, release notes `docs/release-notes-v1.0.0.md`, CREDITS, LICENSE | đạt |
| AC-P4-07 | Mở rộng **Cháy món** (`burn`, `burn_s: 20`): `tests/test_p3_quan_fresh_burn.py`; **Bảng xếp hạng** (`leaderboard`): `tests/test_leaderboard.py`, `tests/test_leaderboard_run_cmd.py` (`run_cmd --export-leaderboard`) | đạt (2/2 mục) |
| AC-P4-08 | Regression P1–P4: [regression.txt](../proof/phase-4/handoff/regression.txt) **132/132 OK**; smoke gather → quan [smoke.md](../proof/phase-4/handoff/smoke.md) 7/7 | đạt |
| AC-P4-09 | Phản tư cá nhân `docs/members/`: NgChiVinh, TrungHieuPh, HoangQuan23112004, khoa-asta | **chưa đủ** — thiếu `22520160.md`, `truclamld.md` tại commit bàn giao |

## Đánh giá ngắn
- Đạt: AC-P4-01 → 08. Chưa đủ: AC-P4-09 (2 phản tư); retro cuối (`docs/retro.md` Phase 4) do truclamld điều phối — chưa có tại commit bàn giao.
- Giới hạn: bench render bằng rasterizer phần mềm offscreen (client thật vẽ canvas trên trình duyệt); soak dùng bot tối giản (`earned` 0).
