# Kế hoạch Phase 4 — Phát hành v1.0.0 (Test Contract v1.3)

- **Mục tiêu:** `contract_version: "1.3"` + `bench_cmd` + `soak_cmd`; 3 cảnh báo có chữ/biểu tượng + chế độ tương phản cao; clone sạch ≤ 3 lệnh; tag `phase-4` và GitHub Release `v1.0.0` (kèm bản đóng gói) cùng trỏ một commit trên `main` trước **3:00**.
- **Mốc:** p15 bench + soak + cảnh báo + clone sạch xong · p20 standup · p25 retro + phản tư đủ 5 người · p27 kiểm commit, tag, Release.

## Phân công

| Vai | Người | Việc | AC |
|---|---|---|---|
| Release / Integrator | nglngnguyen-gh | manifest v1.3 (`bench_cmd`, `soak_cmd`), `chonoi/bench.py`, `chonoi/soak.py` (10 Ngày, kế hoạch D1–D5 lặp), release notes, CHANGELOG theo phase, gói `.zip`, tag + Release | AC-P4-01, 02, 03, 40 |
| Cảnh báo + tương phản | BLong1501 | `chonoi/web/index.html`: chữ/biểu tượng cho **thủy quái gần**, **oxy sắp hết** (< 25%), **khách sắp giận** (kiên nhẫn < 25%); phím bật **tương phản cao**; chơi thử cả 3 cảnh báo ở chế độ đó, lưu ảnh `docs/proof/phase-4/` | AC-P4-10, 11 |
| Đóng gói + Bench/QA | minhtriet061203 | Thử clone sạch (thư mục mới, 3 lệnh README), rà README (yêu cầu môi trường, điều khiển, test, headless, bench), rà `CREDITS.md` / `LICENSE`; chạy regression + bench trên commit bàn giao, lưu artifact | AC-P4-20, 21, 30 |
| Mở rộng | len2412 | Rebase PR #8 `burn` lên v1.2 theo review (giữ cả hai kiểm trong `load_contract()`, "thử giữ lại" bằng `pick_freshest`, 3 test) — mục mở rộng bắt buộc của nhóm 5 người | AC-P4-50 |
| Điều phối retro | LyLe10 | `docs/retro.md` Phase 4: rà hành động P2 (đã làm gì, vướng gì, vì sao), điều tốt / cần sửa / hành động tiếp, một lỗi AI + cách xác minh; tổng hợp số commit theo người | AC-P4-60 |
| Cả nhóm | mọi người | `docs/members/<handle>.md` (≤ 200 từ, dẫn commit), dòng Phase 4 trong `docs/ai-usage-log.md` | AC-P4-61 |

## Rủi ro
- Giao diện chạy trên trình duyệt (`chonoi.live`): `bench_cmd` đo vòng mô phỏng 60 Hz + dựng trạng thái khung hình mà client vẽ, **không đo GPU của trình duyệt** → ghi rõ ở giới hạn đã biết của Release.
- PR #8 trễ → Release ghi mở rộng chưa đạt (nhóm 5 người thiếu mục bắt buộc).
