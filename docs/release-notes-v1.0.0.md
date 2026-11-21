# Quán Ăn Chợ Nổi v1.0.0 — release notes

> **Bản nháp của Integrator (s0ra1n0).** Các ô `☐` chốt ở phút 25–28 trên commit sẽ gắn `phase-4`. Chỉ ghi điều đã chạy thật; mục nào chưa xong thì chuyển xuống "Giới hạn đã biết", không xóa.

Game 2 buổi của Út Sen trên chợ nổi Cà Mau: sáng **Lặn & Hái** (oxy, Máu, cá bơi, Cá Sấu Năm Chèo), tối **Mở Quán** (khách, bếp, giữ chỗ, uy tín), giữa các Ngày là **Shop** nâng cấp. Test Contract **v1.3** (gameplay, tuning, kho và JSONL theo v1.2).

## Điểm mới theo phase
| Phase | Contract | Điểm chính |
|---|---|---|
| 1 | v1.0 | Lặn, oxy/ngạt/Máu/ngất, hái và bắt cá, cập bến ghi kho; quán 1 bếp, khách, phục vụ, tiền, uy tín; headless tất định, JSONL |
| 2 | v1.1 | Cá bơi/sinh theo lịch, Cá Sấu (tuần tra, đuổi, cắn, giật lùi), 2 bếp/4 bàn, 6 món, `--mode day` 5 Ngày, Shop nâng cấp oxy/Máu, pause; mở rộng **burn** (món cháy) |
| 3 | v1.2 | Kho **cá thể** `{id, kind, fresh}`, độ tươi hao theo giây, hàng ươn, giữ chỗ theo id, giá theo độ tươi; HUD độ tươi |
| 4 | v1.3 | `bench_cmd`, `soak_cmd`; ☐ 3 cảnh báo + tương phản cao; ☐ asset SVG + SFX có phụ đề (tự tạo bằng code); ☐ chơi trọn một Ngày trên giao diện (`live --mode day`); LICENSE MIT |

Chi tiết từng thay đổi: [`CHANGELOG.md`](../CHANGELOG.md).

## Cách chạy
Yêu cầu: Python **3.10+**, chỉ thư viện chuẩn, một trình duyệt. Không cần cài gói.
```sh
git clone https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau.git
cd K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau
python3 -m chonoi.live --mode gather      # mở địa chỉ in ra; WASD/mũi tên, E hái/cập bến, Space bắt cá, R chơi lại
```
Từ bản zip đính kèm: giải nén, `cd` vào thư mục, chạy lệnh cuối như trên.

| Việc | Lệnh |
|---|---|
| Test | `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` |
| Headless | `python3 -m chonoi.headless --mode gather\|quan\|day --seed 1 --ticks 600 --out out.jsonl` |
| Benchmark | `python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json` |
| Soak | `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json` |

Windows: dùng `PYTHONPATH="tests;."`; xem ghi chú `python3` trong [`AGENTS.md`](../AGENTS.md).

## Kết quả trên commit phát hành
☐ điền ở phút 25–28 từ `docs/verification/phase-4.md`: số test, `verify.py --phase 4`, `bench.json` (avg / 1% low / load), `soak.json` (days_completed, crashes).

## Giới hạn đã biết
- **Benchmark cần trình duyệt có màn hình** để đo khung hình; máy không có màn hình thì `bench_cmd` thoát mã 1, không ghi số giả.
- **7 module test cũ vẫn chạy trên manifest v1.1 tạm** (`tests/legacy_v11.py`): `test_gather_p1`, `test_lat2`, `test_p2_lat2_fish`, `test_quan_p1`, `test_quan_lat3`, `test_quan_lat4`, `test_quan_p2`. Luật chúng bảo vệ không đổi ở v1.2; phần kho cá thể do `test_fresh_p3`, `test_lat0_v12`, `test_quan_p3`, `test_contract_v13` kiểm trên manifest thật.
- Không làm mở rộng Phase 3 (Khách đặt trước, Dòng nước lũ) và bảng xếp hạng cục bộ.
- ☐ (điền thêm nếu mục Phase 4 nào chưa xong)

## Giấy phép và nguồn
Mã của nhóm theo [MIT](../LICENSE). Khung `chonoi/` ban đầu (headless, inputs, scenario, runner, live, web) do giảng viên cấp cho lab. Đồ họa và âm thanh do nhóm tự tạo bằng code, không dùng asset ngoài; xem [`CREDITS.md`](../CREDITS.md).
