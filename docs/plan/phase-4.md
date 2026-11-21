# Kế hoạch Phase 4 (Ticket-04 "Phát hành v1.0.0", 2:30–3:00)

Người ghi: Võ Hồng Lương (D, Integrator). Nguồn: Ticket-04 trên lab board. Không chép lại số liệu của đề. Trạng thái từng việc ở Google Sheet, tab "Phân công" (dòng P4-xx).

## Đây là gì

Không đổi luật chơi. Phase 4 yêu cầu: **đo hiệu năng cảnh lặn** (`bench_cmd`), **cảnh báo dễ nhận biết** (thủy quái gần, oxy sắp hết, khách sắp giận, có chế độ tương phản cao), **đóng gói và phát hành** (clone sạch chạy bằng tối đa 3 lệnh, GitHub Release `v1.0.0`, `CHANGELOG.md`, `CREDITS.md`, `LICENSE`), và **soak headless** (`soak_cmd`, 10 Ngày trong một tiến trình). `contract_version: "1.3"`. Hạn: tag `phase-4` và Release `v1.0.0` trước 3:00; sau 3:00 là demo (trực tiếp hoặc video `.mp4` dưới 5 phút) và bình chọn.

## Quyết định

1. **`bench_cmd` là đường tối thiểu, trung thực.** Điểm phần benchmark dựa trên việc chạy được lệnh và tạo đúng `bench.json` (năm trường: `avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms`); các mốc 60 FPS, 30 FPS, 10 s chỉ để báo cáo. Giao diện của nhóm chạy trên trình duyệt (`chonoi/web/`), chưa có bộ vẽ ngoài trình duyệt. Hai cách: (a) điều khiển một trình duyệt không giao diện nếu máy có sẵn; (b) bộ vẽ phần mềm đơn giản trong Python vẽ cảnh lặn lên bộ đệm 1280×720. **Chọn (b) làm mặc định** (chạy mọi nơi, chỉ dùng thư viện chuẩn), ghi rõ trong README rằng số FPS là của bộ vẽ phần mềm, không phải của trình duyệt.
2. **Soak dùng chế độ `day` đã có:** 10 Ngày, Ngày 6–10 lặp lại kế hoạch D1–D5, bot hoặc script input tất định, ghi `soak.json` (`days`, `days_completed`, `crashes`, `results[]`, `duration_s`). Soak không ghi bảng xếp hạng.
3. **Cảnh báo là chữ hoặc biểu tượng,** không chỉ màu; thêm một cờ tương phản cao trong UI; có test đọc snapshot để chứng minh điều kiện kích hoạt.
4. **Clone sạch trên macOS hoặc Linux:** chứng minh bằng GitHub Actions chạy trên Ubuntu (ngoài máy Windows của nhóm), ghi liên kết lần chạy vào bằng chứng.
5. **Release là việc đối ngoại:** D chuẩn bị bản đóng gói và release notes, người dùng đồng ý rồi mới đẩy tag và tạo Release.
6. **Mở rộng (bảng xếp hạng cục bộ, phụ đề SFX) là tùy chọn;** chỉ làm khi lõi xong.

## Phân tích tác động

| Module | File cần đổi | Test bị ảnh hưởng | Người phụ trách |
|---|---|---|---|
| Contract v1.3 | `game.contract.json` (`bench_cmd`, `soak_cmd` ở gốc), `chonoi/contract.py` | `tests/test_contract_v11.py` (phiên bản hỗ trợ) | D |
| Bench | `tools/bench.py` hoặc `chonoi/bench.py` (mới), `docs/proof/phase-4/bench.json` | thêm test chạy lệnh và kiểm cấu trúc `bench.json` | A |
| Soak | `chonoi/soak.py` hoặc `tools/soak.py` (mới), `docs/proof/phase-4/soak.json` | thêm test chạy 10 Ngày | D |
| Cảnh báo, tương phản cao | `chonoi/web/index.html`, `chonoi/live.py` | `tests/test_live.py`, test điều kiện kích hoạt | C |
| Đóng gói | `README.md`, `CHANGELOG.md`, `CREDITS.md`, `LICENSE`, workflow CI trên Ubuntu | không | B |
| Bằng chứng, Release | `docs/verification/phase-4.md`, `docs/retro.md`, `docs/members/<handle>.md`, tag `phase-4`, GitHub Release `v1.0.0` | hồi quy P1–P3 | D (retro: C điều phối) |

## Việc, người, phụ thuộc (mã AC theo Sheet)

| AC | Việc | Người | Phụ thuộc |
|---|---|---|---|
| AC-P4-01 | Contract v1.3, khai `bench_cmd` và `soak_cmd` | D | Phase 3 xong |
| AC-P4-02 | Benchmark có render, xuất `bench.json` đúng cấu trúc | A | AC-P4-01 |
| AC-P4-03 | Soak headless 10 Ngày, xuất `soak.json` | D | AC-P4-01 |
| AC-P4-04 | Ba cảnh báo dễ nhận biết và chế độ tương phản cao, có test | C | không |
| AC-P4-05 | Đóng gói: README ≤ 3 lệnh, `CHANGELOG.md`, `CREDITS.md`, `LICENSE`, CI Ubuntu | B | không |
| AC-P4-06 | Thử clone sạch bằng tối đa 3 lệnh, lưu bằng chứng | D | AC-P4-05 |
| AC-P4-07 | Retro rà hành động Phase 2, hồ sơ cá nhân đủ người, đánh giá chéo | C điều phối, cả nhóm | không |
| AC-P4-08 | Hồi quy P1–P3, `docs/verification/phase-4.md`, tag `phase-4`, Release `v1.0.0` | D | tất cả |

Lịch (theo Ticket-04): phút 0–15 đo bench, cảnh báo, thử clone sạch, hồi quy, chuẩn bị Release song song; 15–25 retro và phản tư cá nhân, standup phút 20; 25–30 dự phòng và kiểm commit, artifact, tag, Release; hạn `phase-4` và `v1.0.0` là 3:00. Sau 3:00: demo.

## Demo sau 3:00 (checklist của đề)

Chơi một Ngày từ Lặn và Hái qua Mở Quán đến khi đóng Shop; chạy test và cho thấy kết quả đạt; chỉ ra bằng chứng chia việc, phối hợp và đóng góp của từng người trong repo; mở ma trận truy vết. Người trình bày: D (ma trận, test), A (chơi), B và C (bằng chứng đóng góp).

## Rủi ro

- **Hạn 3:00 cứng và rất ngắn (30 phút):** làm trước những gì không phụ thuộc code: README, `CHANGELOG.md`, `CREDITS.md`, `LICENSE`, khung `docs/verification/phase-4.md`, hồ sơ cá nhân (đừng để dồn).
- **Bench có render:** bộ vẽ phần mềm bằng Python sẽ chậm; số FPS thấp nhưng thật; ghi trung thực, không bịa số. Nếu không kịp, ít nhất chạy được lệnh và xuất đúng `bench.json`.
- **Số commit và tài khoản:** B và C cần đủ ≥ 3 commit bằng tài khoản có trong `TEAM.md` (xem `docs/verification/phase-1.md`, AC-P1-24 và AC-P1-25); tài khoản của B (`HoAnhTu245` và `TuHoAnh`) cần xác nhận.
- **Hồ sơ cá nhân:** `docs/members/<handle>.md` đúng tên handle, ≤ 200 từ, có link commit; hồ sơ của B đang đặt tên theo mã số.
- **Release đối ngoại:** cần người dùng đồng ý trước khi tạo; gắn tag trên đúng commit `main` đã chạy test.
- **Retro:** retro Phase 2 phải được ghi sớm (Ticket-02 mục 5) thì Phase 4 mới rà được; nếu bỏ qua, bảng "rà hành động Phase 2" trống.

## Câu hỏi cho PO

- Bench có chấp nhận bộ vẽ phần mềm không giao diện (số FPS không phải của trình duyệt)?
- `LICENSE` nào cho phép (nhóm tự chọn, tài sản ngoài phải CC0, CC-BY hoặc MIT)?
