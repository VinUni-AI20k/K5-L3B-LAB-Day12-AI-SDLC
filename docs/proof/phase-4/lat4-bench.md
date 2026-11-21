# Lát 4 — Benchmark Phase 4 (AC-P4-02)

**Người thực hiện:** `nguyenhung1901` · **Cơ sở:** Ticket-04 / `docs/plan/phase-4.md`.

## Code và cách đo

- `chonoi/bench.py`: dùng `LiveGame`/`LiveServer` thật ở mode `gather`, seed theo CLI, HTTP nội bộ, mở browser để đo. Không mô phỏng khung hình bằng vòng lặp Python.
- `chonoi/web/index.html`: phần `// --- bench (Hùng)`, khi `?bench=1` render canvas cố định **1280×720**, không nhận input để nhân vật đứng yên ở bến. Đợi có snapshot cảnh Gather, làm nóng **3 giây**, thu khoảng cách thời gian `requestAnimationFrame` trong `--duration` giây rồi gửi `/bench`.
- Server tính `frames`, `measured_s` từ mẫu frame, `avg_fps = frames/measured_s`, `p1_low_fps = 1 / trung bình thời gian 1% khung chậm nhất` (làm tròn số lượng khung lên), `load_ms` từ lúc chạy Python đến lúc server nhận thông báo khung scene đầu tiên. Độ trễ gửi thông báo HTTP có thể làm `load_ms` lớn hơn thời gian hiển thị thực một ít.
- Kết quả chỉ được ghi khi nhận mẫu hợp lệ đủ thời gian; thiếu browser/timeout → mã 1, không tự tạo số liệu.
- **Hỗ trợ HUD quán:** thêm cảnh báo chữ “Khách sắp giận” (bàn liên quan) khi khách còn chờ và kiên nhẫn dưới 25%. Đây chỉ là một trong ba cảnh báo của AC-P4-04; cần Tiệp kiểm thử giao diện và chế độ tương phản cao.

## Kiểm tra đã thực hiện trên snapshot

- `python -m unittest discover -s tests -p "test_bench_p4.py" -v`: **6/6 PASS**; kiểm công thức, validation, HTTP API, cảnh chuẩn (cá/Cá Sấu/nhân vật ở bến), từ chối browser không có và từ chối đo thiếu thời gian.
- `node --check` đối với JavaScript trích từ `index.html`: **PASS** (chỉ kiểm cú pháp).
- **Chưa có kết quả FPS thật trên máy này:** Chromium ở môi trường kiểm thử bị chính sách chặn điều hướng đến HTTP localhost. Không tạo `bench.json` giả. Đánh giá AC-P4-02 cần chạy trực tiếp trên desktop có browser và lưu file JSON thật.

## Lệnh chạy và lưu bằng chứng (Windows, tại repo)

```powershell
python -m chonoi.bench --seed 42 --duration 30 --out docs/proof/phase-4/bench.json
python -m unittest discover -s tests -p "test_bench_p4.py" -v
```

Nếu Chrome/Edge không mở đúng cửa sổ, có thể chỉ định executable trình duyệt:

```powershell
$env:CHONOI_BENCH_BROWSER = "C:\Program Files\Google\Chrome\Application\chrome.exe"
python -m chonoi.bench --seed 42 --duration 30 --out docs/proof/phase-4/bench.json
```

Sau lần chạy **thành công**: đối chiếu `bench.json` có đúng 5 trường; giữ nguyên số thực, ghi ngưỡng báo cáo `avg_fps >= 60`, `p1_low_fps >= 30`, `load_ms <= 10000` (không phải điều kiện chấm lệnh). Khi fail không dùng file bench từ lượt cũ. QA/Integrator kiểm chứng lại trên commit định gắn `phase-4`.

## Phụ thuộc chung

Integrator (Lát 0) thêm `bench_cmd: "python3 -m chonoi.bench"` vào `game.contract.json` v1.3; chủ README bổ sung lệnh. UI/QA tiếp tục triển khai ba cảnh báo và tương phản cao. Không tự gắn tag hoặc công bố Release.
