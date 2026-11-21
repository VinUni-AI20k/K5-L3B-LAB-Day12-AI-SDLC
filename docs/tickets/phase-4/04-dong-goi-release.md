# 04: Đóng gói + Release `v1.0.0` + contract 1.3

**What to build:** Người lạ clone repo về, chạy 3 lệnh là chơi được; GitHub có Release `v1.0.0` kèm gói chạy được, release notes và CHANGELOG đầy đủ; `game.contract.json` khai đúng `bench_cmd`/`soak_cmd` ở `contract_version: "1.3"`.

**Blocked by:** 01, 02, 03

**Status:** ready-for-agent

- [ ] `contract_version: "1.3"` + `bench_cmd` + `soak_cmd` ở gốc manifest; **không** đổi tuning/kho/JSONL (v1.2 giữ nguyên).
- [ ] Clone sạch vào thư mục tạm, chạy **đúng 3 lệnh** trong README (macOS/Linux) và chơi được; ghi ảnh + log.
- [ ] README ghi: yêu cầu môi trường (Python 3.10+, trình duyệt cho bench), điều khiển, lệnh test, headless, bench, soak.
- [ ] Gói phát hành (zip không kèm `.git`) đính vào GitHub Release `v1.0.0`.
- [ ] Release notes do nhóm viết: điểm mới, cách chạy, giới hạn đã biết.
- [ ] `CHANGELOG.md` đủ theo phase; `CREDITS.md` + file LICENSE rà lại cho mọi asset đã dùng.
- [ ] Tag `phase-4` và Release `v1.0.0` **cùng một commit** trên `main`; kiểm bằng `git rev-parse phase-4^{}` so với commit của Release.
