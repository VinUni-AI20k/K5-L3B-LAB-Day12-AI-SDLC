# Kế hoạch Phase 4 — TICKET-04 "Phát hành v1.0.0" (Contract v1.3)

- **Khung giờ:** 30 phút (2:30–3:00). **Hạn:** tag `phase-4` **và** GitHub Release `v1.0.0` cùng trỏ tới một commit trên `main` trước 3:00.
- **Mục tiêu:** benchmark có render (`bench_cmd`), soak 10 Ngày (`soak_cmd`), 3 cảnh báo dễ nhận biết + chế độ tương phản cao, chạy từ clone sạch trong ≤ 3 lệnh, Release có bản đóng gói, retro và phản tư đủ 7 người.
- Gameplay, tuning, kho và JSONL **giữ nguyên v1.2**. Phase 4 không đổi luật.

## 0. Phút 0–3: chốt quyết định (Integrator chốt, PO ghi `docs/adr/0003-bench-va-dong-goi.md`)

1. **Cách đo bench có render.** Client hiện là web (`chonoi/web/`, vẽ bằng `requestAnimationFrame`), nên phải đo trong trình duyệt:
   - **Đề xuất:** `python3 -m chonoi.bench` bật server live ở chế độ bench, mở Chromium headless bằng Playwright ở 1280×720, nạp `/?bench=1&seed=42`. Client chạy cảnh lặn lõi (độ tươi, cá bơi, Cá Sấu, hiệu ứng mặc định, Út Sen đứng ở bến), làm nóng 3 s, ghi thời gian từng khung trong 30 s rồi POST về server. Python tính 5 trường và ghi `bench.json`.
   - **Dự phòng** nếu không cài được Playwright: mở trình duyệt mặc định bằng `webbrowser`, canvas cố định 1280×720, client vẫn POST kết quả. Cách này không cần thêm thư viện nhưng cần máy có màn hình.
   - Công thức: `avg_fps = frames / measured_s`; `p1_low_fps` = nghịch đảo thời gian trung bình của `max(1, ceil(0.01 × frames))` khung chậm nhất (tính bằng giây); `load_ms` từ lúc khởi chạy lệnh tới khung đầu của cảnh đo.
2. **Bot soak:** tất định và rẻ nhất có thể. Mỗi Ngày: gather `interact` ở frame 0 (cập bến ngay), quán không điều khiển, Shop `shop_done` ngay. Kế hoạch D1–D5 lặp ở Ngày 6–10. Bắt mọi exception theo Ngày để đếm `crashes` thay vì dừng tiến trình.
3. **Bản đóng gói:** file zip mã nguồn kèm `README` và lệnh chạy (Python 3, không cần build). Tên `cho-noi-v1.0.0.zip`.
4. **Danh tính commit:** trên `main` có 9 commit tên tác giả "Hai Duong", không khớp ai trong `TEAM.md`. Người đó xác nhận đó là tài khoản của ai và ghi vào phản tư, vì commit của người không có trong `TEAM.md` không được tính.

## 1. Chia việc theo vai của ticket

| Vai | Việc | File / đầu ra | Người |
|---|---|---|---|
| **Release / Integrator** | Đặt `contract_version:"1.3"`, khai `bench_cmd`, `soak_cmd` ở gốc `game.contract.json`. Gộp PR, kiểm commit bàn giao, rà `CHANGELOG.md` theo từng phase, viết release notes (điểm mới, cách chạy, giới hạn đã biết), gắn tag `phase-4` và công bố Release v1.0.0 kèm zip | `game.contract.json`, `CHANGELOG.md`, GitHub Release | **invzble-z** |
| **Soak** | `chonoi/soak.py`: `--seed --days --out`, chạy N Ngày trong một tiến trình qua `DaySim`, ghi `soak.json {days, days_completed, crashes, results[{day,earned,reputation,score}], duration_s}`. Tiền, uy tín, cấp nâng cấp, id cá thể tiếp tục xuyên Ngày | `chonoi/soak.py`, `tests/test_p4_soak.py` (chạy 2 lần cùng seed → các trường gameplay giống nhau) | **Quoosc** (pair với invzble-z vì phụ thuộc `day.py`) |
| **Bench (phía Python)** | `chonoi/bench.py`: bật server, mở trình duyệt theo quyết định 0.1, nhận kết quả, tính 5 trường, ghi `bench.json`, mã khác 0 nếu lỗi | `chonoi/bench.py`, `tests/test_p4_bench.py` (kiểm công thức `p1_low_fps` trên dãy khung giả) | **ttkien0710** |
| **Bench (phía client)** | Chế độ `?bench=1`: dựng cảnh lặn chuẩn seed 42, đứng yên ở bến, làm nóng 3 s, đo 30 s, gửi thời gian khung | `chonoi/web/js/` | **nganhduong123** |
| **Cảnh báo + tương phản cao** | Chữ và biểu tượng cho: thủy quái gần ("Thủy quái!" + viền tím), oxy sắp hết (< 25%, "Hết hơi!"), khách sắp giận (kiên nhẫn < 25%). Nút bật tắt chế độ tương phản cao (màu nền/chữ đậm, không chỉ dựa vào màu), lưu lựa chọn | `chonoi/web/` | **nganhduong123** |
| **Chơi thử cảnh báo** | Chơi thử cả 3 cảnh báo ở chế độ tương phản cao, chụp ảnh từng cảnh báo, báo lỗi cho Dương. Hoàn thiện phần còn thiếu của `monsters.py` nếu chưa xong (không có Cá Sấu thì không có cảnh báo thủy quái) | `docs/proof/phase-4/alerts-*.png` | **comtrang378-ship-it** |
| **Đóng gói** | Thử từ clone sạch trên macOS hoặc Linux (WSL được): ≤ 3 lệnh chạy được bản có giao diện. Ghi lại vào `README.md`: yêu cầu môi trường, điều khiển, lệnh test, headless, bench, soak. Tạo `cho-noi-v1.0.0.zip` và thử giải nén chạy lại. Rà `CREDITS.md` và `LICENSE` | `README.md`, `docs/proof/phase-4/clean-clone.txt`, zip | **NguyenQuangDunghe161764** |
| **Bench / QA** | Chạy bench (seed 42, 30 s) và lưu `bench.json`. Chạy soak `--seed 7 --days 10`. Regression P1–P3 còn hiệu lực. Ma trận AC-P4-xx → bằng chứng → kết quả | `docs/proof/phase-4/`, `docs/verification/phase-4.md` | **WorkOfMinh** |
| **Điều phối retro** | Mở retro bằng việc rà hành động đã chốt ở retro P2. Tổng hợp bằng chứng đóng góp (`git shortlog -sn --no-merges`, PR, phần mỗi người làm). Ghi một lỗi AI đã mắc và cách nhóm xác minh. Cập nhật `docs/clarify.md`, `docs/ai-usage-log.md` | `docs/retro.md` | **nganhduong123** |
| **Phản tư cá nhân** | Mỗi người viết `docs/members/<handle>.md` (≤ 200 từ): phần mình làm, đã giúp ai, AI sai ở đâu, bài học, dẫn commit | `docs/members/*.md` | **cả 7 người** |

> Dương nhận nhiều việc trong `chonoi/web/`. Nếu chậm ở phút 15, Kiên (đã xong `bench.py`) sang làm chế độ tương phản cao; Dương giữ bench client và retro.

## 2. Mốc giờ

| Phút | Việc |
|---|---|
| 0–3 | Chốt mục 0, ghi ADR 0003. Bào đẩy `contract_version:"1.3"` với `bench_cmd`/`soak_cmd` |
| 3–15 | Song song: bench (Kiên + Dương), soak (Quốc + Bào), cảnh báo/tương phản (Dương, Tú chơi thử), clone sạch + README (Dũng), regression (Minh). Bào viết release notes nháp |
| 15–25 | Retro (Dương điều phối) và phản tư cá nhân của cả 7 người. **Phút 20: standup**, rà vướng, điều người xong sang hỗ trợ. Minh chạy bench + soak trên bản tích hợp, điền `docs/verification/phase-4.md` |
| 25–30 | Dự phòng. Bào kiểm commit, artifact, zip. **Gắn tag `phase-4` và công bố Release v1.0.0 trên cùng commit, ≤ 3:00** |

## 3. AC-P4

| AC | Nội dung | Bằng chứng | Người |
|---|---|---|---|
| AC-P4-01 | `contract_version:"1.3"`, khai đúng `bench_cmd`, `soak_cmd` | `game.contract.json` | invzble-z |
| AC-P4-02 | `bench_cmd --seed 42 --duration 30 --out bench.json` chạy cảnh chuẩn, đủ 5 trường đúng công thức | `docs/proof/phase-4/bench.json` | ttkien0710, nganhduong123 |
| AC-P4-03 | `soak_cmd --seed 7 --days 10`: `days_completed = 10`, `crashes = 0`, chạy lặp giống nhau ở trường gameplay | `docs/proof/phase-4/soak.json` | Quoosc |
| AC-P4-04 | 3 cảnh báo có chữ hoặc biểu tượng, chế độ tương phản cao hoạt động | ảnh chụp | nganhduong123, comtrang378-ship-it |
| AC-P4-05 | Clone sạch chạy bản giao diện trong ≤ 3 lệnh, README đủ thông tin | `clean-clone.txt` | NguyenQuangDunghe161764 |
| AC-P4-06 | Regression P1–P3 còn hiệu lực đạt | log test | WorkOfMinh |
| AC-P4-07 | CHANGELOG theo phase, release notes, zip, tag `phase-4` và Release v1.0.0 cùng commit | GitHub Release | invzble-z |
| AC-P4-08 | Retro rà hành động P2, đủ 7 phản tư cá nhân | `docs/retro.md`, `docs/members/` | nganhduong123, cả nhóm |

## 4. Mở rộng
- Theo giả định ở `docs/clarify.md` #2, nhóm 7 người cần ≥ 2 mục **cho cả buổi lab**. Đang có `burn` (Kiên, P2). Mục thứ hai chọn rẻ nhất:
  - `leaderboard`: Quốc làm sau khi xong soak (cùng dùng `DaySim` 5 Ngày). Cần `--leaderboard` + `--player-name` ở headless `day`, top 10 lưu bền, `--export-leaderboard`.
  - Hoặc `snake` (Tú, P2) nếu `monsters.py` đã chạy ổn.
- Không làm phụ đề SFX vì game chưa có âm thanh.
- Mọi mục mở rộng phải có test, bằng chứng và được khai trong `extensions` + README. Hết giờ thì bỏ, không để lõi đỏ.

## 5. Demo sau 3:00 (chuẩn bị song song, Minh giữ checklist)
- Chơi một Ngày từ Lặn & Hái qua Mở Quán tới đóng Shop: nganhduong123 lái.
- Chạy test và cho thấy kết quả đạt: WorkOfMinh.
- Bằng chứng chia việc và đóng góp từng người: `docs/plan/`, `git shortlog`, `docs/members/`.
- Mở ma trận truy vết `docs/verification/phase-1..4.md` và chỉ bằng chứng tương ứng.

## 6. Rủi ro
- **Soak và Release phụ thuộc `day.py`** (nợ P2). Nếu tới 2:30 vẫn chưa có `day`, `soak_cmd` không đạt. Ghi trung thực trong verification và release notes ("giới hạn đã biết").
- Playwright cần tải trình duyệt, có thể làm clone sạch vượt 3 lệnh. Bench là lệnh riêng nên không tính vào 3 lệnh chạy game, nhưng phải ghi rõ trong README.
- Chỉ người có quyền trên repo (invzble-z) tạo được Release. Nếu Bào vắng, người dự phòng là WorkOfMinh, và cần được cấp quyền trước 2:55.
