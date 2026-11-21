# P4-07 · Thử clone sạch và hồi quy Phase 1–3 (AC-P4-06)

Chạy ngày 2026-11-21, commit `a887cec` của `main` (sau PR #56, contract 1.3).

## 1. Clone sạch bằng đúng 3 lệnh của README (máy Windows, clone từ GitHub)

```bash
git clone https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn.git   # lệnh 1: thư mục tạm mới, không có file nào của máy dev
cd K5-L3B-LAB-Day12-AI-SDLC-NgheAn                                              # lệnh 2
python -m chonoi.live                                                           # lệnh 3 (Windows gõ `python`, macOS/Linux gõ `python3`)
```

Lệnh 3 in `Mở trình duyệt tại http://127.0.0.1:<cổng>/  (chế độ menu, seed 1)`. Không cài thêm gói nào. Lệnh headless trong README (`--mode day --days 1 --seed 1 --ticks 600`) thoát mã 0 và dòng `end` hợp lệ.

## 2. Hồi quy Phase 1–3 và hai lệnh của contract 1.3, chạy trong chính bản clone sạch đó

| Lệnh | Kết quả |
|---|---|
| `PYTHONPATH=tests:. python -m unittest discover -s tests` | 377 test, OK |
| `tools/smoke_phase1.py` | 27/27 |
| `tools/smoke_phase2.py` | 15/15 |
| `tools/smoke_phase3.py` | 13/13 |
| `tools/check_determinism.py` | gather, quan, day giống từng byte |
| `tools/check_no_hardcode.py` | OK |
| `bench_cmd --seed 42 --duration 1 --warmup 0 --out b.json` | thoát 0, đủ 5 trường |
| `soak_cmd --seed 7 --days 2 --out s.json` | thoát 0, `days_completed` 2, `crashes` 0 |

## 3. CI Ubuntu (bằng chứng ngoài máy Windows)

`.github/workflows/ci.yml` chạy trên `ubuntu-latest` (Ubuntu 26.04, Python 3.12) và nay gồm các bước: kiểm thành viên, build, toàn bộ test, **clone sạch theo README (3 lệnh)**, **hồi quy Phase 1–3** (ba smoke, tất định, hard-code) và **`bench_cmd`, `soak_cmd` bản ngắn**.

- Lần chạy đủ các bước mới, nhánh `p4-07-clean-clone` (workflow_dispatch): [run 44918861655](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/actions/runs/44918861655): thành công, 377 test, smoke 27/27, 15/15, 13/13, bước clone sạch in địa chỉ máy chủ và headless day ra dòng `end`, bench và soak chạy ra JSON.
- Lần chạy trên `main` (có bước clone sạch, chưa có bước hồi quy mới): [run 44918780735](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/actions/runs/44918780735): thành công.
- Sau khi PR này vào `main`, lần chạy `push main` kế tiếp là bằng chứng chính thức cho commit gắn tag `phase-4` (ghi lại ở P4-09).

## Giới hạn (nói thẳng)
- Chưa thử trên máy macOS hay Linux thật của người dùng; Ubuntu chỉ qua CI. Lệnh 3 chỉ kiểm máy chủ khởi động và in địa chỉ, không mở trình duyệt hay chơi trong CI (giao diện đã xem tay trên Windows ở P2-08 và P3).
- `bench_cmd` bản ngắn (1 giây) ở CI, không phải lần đo 30 giây; số đo chính thức ở `docs/proof/phase-4/bench.json`.
