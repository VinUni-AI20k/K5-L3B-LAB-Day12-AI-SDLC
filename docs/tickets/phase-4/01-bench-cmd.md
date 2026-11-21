# 01: `bench_cmd` — đo FPS thật và xuất `bench.json`

**What to build:** Một lệnh chạy cảnh chuẩn trong trình duyệt thật (1280×720, có render), làm nóng rồi đo 30 giây, và ghi `bench.json` đúng 5 trường để người chấm so sánh giữa các nhóm.

**Blocked by:** P2-02 (cá bơi), P3-01 (độ tươi) — cảnh đo phải đủ

**Status:** ready-for-agent

- [ ] `<bench_cmd> --seed 42 --duration 30 --out bench.json` chạy được; tự tìm trình duyệt (`CHROME`/`chromium`/`chrome`), không có thì mã thoát 2 kèm thông báo.
- [ ] Cảnh đo: buổi sáng lõi, Út Sen đứng yên ở bến, cá bơi + Cá Sấu + hiệu ứng mặc định; cửa sổ 1280×720; seed theo cờ.
- [ ] Làm nóng 3 s (không tính), đo `duration` giây; ghi `frames`, `measured_s`, `avg_fps = frames/measured_s`.
- [ ] `p1_low_fps`: lấy `n = max(1, ceil(0.01 × frames))` khung chậm nhất, `1 / (tổng thời gian n khung / n)`.
- [ ] `load_ms`: từ lúc khởi chạy tới khung hình đầu tiên của cảnh đo.
- [ ] File chỉ có đúng 5 trường; đóng trình duyệt và server sạch sau khi đo (không treo tiến trình).
- [ ] Artifact `bench.json` + log lưu vào `docs/proof/phase-4/`; báo cáo mốc `avg ≥ 60`, `1% low ≥ 30`, `load ≤ 10 s` (không đạt thì ghi trung thực).
