# TICKET-04 — Phát hành v1.0.0 (Phase 4) · Test Contract v1.3

> Chép từ lab board (phát hành 11:29, hạn tag `phase-4` và GitHub Release v1.0.0 lúc 3:00). Nguồn chuẩn cho Phase 4.

30 phút (2:30–3:00) · Test Contract v1.3 · Hạn đẩy tag phase-4 và công bố GitHub Release v1.0.0 3:00.

Đo hiệu năng của cảnh lặn, kiểm tra cách người chơi nhận cảnh báo, bàn giao bản chạy được từ repo sạch và tổng kết cách nhóm đã làm việc.

## 1. Lõi (mọi nhóm)
### Benchmark có render
`<bench_cmd> --seed 42 --duration 30 --out bench.json`

| Cấu hình | Giá trị |
|---|---|
| Cảnh đo | Buổi sáng lõi với độ tươi, cá bơi, Cá Sấu Năm Chèo và hiệu ứng mặc định. Út Sen đứng yên ở bến. |
| Seed | 42. |
| Cửa sổ | 1280×720. |
| Làm nóng / đo | Làm nóng 3 s, sau đó đo 30 s. |

Runner gọi `<bench_cmd> --seed <int> --duration <giây> --out <bench.json>`. Xuất năm trường JSON: `{"avg_fps":72,"p1_low_fps":38,"frames":2160,"measured_s":30,"load_ms":2400}` (minh họa).

| Trường | Cách tính |
|---|---|
| frames, measured_s | Số khung hình và số giây thực tế trong khoảng đo sau làm nóng. |
| avg_fps | frames / measured_s. |
| p1_low_fps | Chọn max(1, ceil(0.01 × frames)) khung chậm nhất rồi lấy nghịch đảo thời gian trung bình của chúng, tính thời gian theo giây. |
| load_ms | Mili giây từ lúc khởi chạy đến khung hình đầu tiên của cảnh đo. |

Điểm phần benchmark dựa trên việc chạy được lệnh và tạo đúng bench.json. Mốc avg ≥ 60 FPS, 1% low ≥ 30 FPS và load ≤ 10 s dùng để báo cáo. Lưu artifact từ commit nộp trong docs/proof/phase-4/.

### Cảnh báo dễ nhận biết
Dùng chữ hoặc biểu tượng để người chơi nhận ra thủy quái gần, oxy sắp hết và khách sắp giận. Thêm chế độ tương phản cao và chơi thử cả ba cảnh báo ở chế độ đó.

### Đóng gói và phát hành
Từ clone sạch, chạy được bản có giao diện theo README.md trong tối đa 3 lệnh trên macOS hoặc Linux. Ghi yêu cầu môi trường, điều khiển, lệnh test, lệnh headless và benchmark. Đính kèm bản đóng gói chạy được ở GitHub Release v1.0.0. Release notes do nhóm viết, nêu điểm mới, cách chạy và giới hạn đã biết. CHANGELOG.md ghi theo từng phase. Rà CREDITS.md và LICENSE cho tài sản đã dùng. Đặt contract_version:"1.3", khai bench_cmd và soak_cmd ở gốc game.contract.json. Gameplay, tuning, kho và JSONL theo v1.2.

## 2. Soak headless (giảng viên chạy để báo cáo)
`<soak_cmd> --seed 7 --days 10 --out soak.json` — nhận `--seed <int> --days <N> --out <soak.json>`. Giảng viên chạy 10 Ngày trong một tiến trình headless bằng script input hoặc bot tất định. Mỗi Ngày đi qua gather → quan → shop. Kế hoạch D1–D5 lặp ở Ngày 6–10. Tiền, tổng thu, uy tín, cấp nâng cấp, số Ngày và id cá thể tiếp tục xuyên suốt. soak.json có days, days_completed, crashes, results, duration_s; mỗi results[] có day, earned, reputation, score lúc Shop đóng. Đạt khi days_completed = days và crashes = 0. So tính lặp ở các trường gameplay, bỏ số đo thời gian thực. Không chấm ngưỡng bộ nhớ.

## 3. Mở rộng
Nhóm 4 người không bắt buộc, nhóm 5 ít nhất 1 mục, nhóm 6 ít nhất 2 mục. Nếu làm, ghi vào README và lưu bằng chứng. Tự do sáng tạo: tắt phần tự thêm ở headless hoặc giữ nguyên kết quả theo Test Contract; ghi vào “Sáng tạo của nhóm” trong README.md kèm bằng chứng lõi vẫn đúng.
- **Bảng xếp hạng cục bộ (leaderboard):** top 10 cục bộ bền vững; một mục mỗi lượt chuẩn đủ 5 Ngày; sắp điểm giảm dần, hòa thì mục ghi trước đứng trước. `<run_cmd> --export-leaderboard <out.json> [--leaderboard <store.json>]` xuất `{"entries":[{"name","score","days_completed","seed"}]}`. Headless day nhận cặp `--leaderboard <store.json> --player-name <name>`; ghi đúng một mục khi đủ 5 Ngày chuẩn, không scenario, reason "days_complete"; thiếu một cờ hoặc sai mode → mã 2. Soak không ghi xếp hạng.
- **Phụ đề SFX:** hiện phụ đề cho các hiệu ứng âm thanh; chơi thử với âm thanh tắt.

## 4. Quy trình nhóm
Cùng commit vào fork chung bằng tài khoản GitHub của từng người; ghi Co-authored-by khi cùng làm một commit. Vai: Đóng gói · Bench/QA (docs/verification/phase-4.md) · Release/Integrator (release notes, CHANGELOG, tag, Release) · Điều phối retro (rà hành động P2, tổng hợp bằng chứng đóng góp). Ghi AC-P4-xx → bằng chứng → kết quả trên commit bàn giao trong docs/verification/phase-4.md. Cập nhật docs/clarify.md và docs/ai-usage-log.md. Retro mở đầu bằng rà hành động P2; ghi điều làm tốt, cần sửa, hành động tiếp; nêu một lỗi AI và cách xác minh. Mỗi người viết docs/members/<handle>.md (≤ 200 từ). Đẩy phase-4 và công bố Release v1.0.0 từ cùng commit trên main trước khi hết giờ build.

| Phút | Việc |
|---|---|
| 0–15 | Đo bench, cảnh báo + tương phản, thử clone sạch, regression, chuẩn bị Release. |
| 15–25 | Retro và phản tư cá nhân; phút 20 standup. |
| 25–30 | Dự phòng, kiểm commit, artifact, tag, Release. Hạn 3:00. |

## DoD
- [ ] Contract v1.3 khai đúng lệnh. bench_cmd chạy cảnh chuẩn và tạo bench.json đúng cấu trúc. soak_cmd sẵn sàng cho runner lớp.
- [ ] Clone sạch chạy bằng tối đa 3 lệnh. Ba cảnh báo có chữ hoặc biểu tượng và chế độ tương phản cao hoạt động.
- [ ] Regression P1–P3 còn hiệu lực đạt. docs/verification/phase-4.md và bằng chứng khớp commit gắn tag. Ghi chép làm rõ và nhật ký AI đã cập nhật.
- [ ] CHANGELOG.md, release notes và bản đóng gói đầy đủ. Tag phase-4 và GitHub Release v1.0.0 cùng trỏ tới commit trên main, chậm nhất 3:00.
- [ ] Retro đã rà hành động P2 và chốt việc tiếp theo. Có phản tư cá nhân đủ người và bằng chứng đóng góp của từng người trong repo chung.
- [ ] Nếu làm mở rộng, có bài kiểm và bằng chứng cho từng mục.

## Demo sau giờ build
Sau 3:00, demo trực tiếp hoặc video .mp4 < 5 phút: chơi một Ngày từ Lặn & Hái qua Mở Quán đến khi đóng Shop; chạy test và cho thấy đạt; chỉ ra bằng chứng chia việc/đóng góp của từng người; mở ma trận truy vết và bằng chứng tương ứng.
