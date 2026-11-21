# Ma trận truy vết Phase 4 — Phát hành v1.0.0 (contract v1.3)

> Nguyên tắc: Bằng chứng phải thật tại thời điểm kiểm tra. Không ghi nhận "Đạt" khi chưa có artefact thật trong repo.

Cách kiểm chung: `python tools/run_checks.py`, `python tools/bench.py`, chạy headless 10 ngày soak test, và kiểm tra live UI tương phản cao.
Bằng chứng thô: `docs/proof/phase-4/`. Cột Kết quả ghi trạng thái trung thực tại commit kiểm tra hiện tại.

## Ma trận Acceptance Criteria Phase 4 (AC-P4)

| AC | Mô tả yêu cầu | Cách kiểm tra | Bằng chứng kiểm chứng | Kết quả |
|---|---|---|---|---|
| **AC-P4-01** | `bench_cmd` đo FPS cảnh chuẩn 1280×720 (3s warm-up, 30s đo), xuất `bench.json` đúng 5 trường (`avg_fps, p1_low_fps, frames, measured_s, load_ms`), mã thoát 2 nếu thiếu Chrome | `python tools/bench.py --seed 42 --duration 30 --out bench.json` | Cần `docs/proof/phase-4/bench.json` | **Chưa đạt** (Đã có `tools/bench.py` do Văn Minh viết; chưa chạy 30s trên trình duyệt thật để commit artefact `bench.json`) |
| **AC-P4-02** | `soak_cmd` chạy 10 Ngày headless bằng bot tất định không crash (`crashes == 0`, `days_completed == 10`), ghi `soak.json` | Chạy 10 ngày liên tục với bot tự động qua 3 pha gather → quan → shop | Cần `docs/proof/phase-4/soak.json` | **Chưa đạt** (Chưa có `tools/soak.py`, chưa có `soak_cmd` trong manifest, chưa có artefact `soak.json`) |
| **AC-P4-03** | 3 Cảnh báo nguy hiểm nhận biết ngay bằng chữ + biểu tượng (không phụ thuộc màu): 🐊 Thủy quái gần, 🫁 Hết hơi, 😡 Khách sắp giận. Đọc tốt trong Chế độ tương phản cao (phím `C`, `?hc=1`) | Mở trình duyệt thử 3 tình huống với phím `C`, nút HUD `👁️ Tương phản` và `?hc=1` | `docs/proof/phase-4/canh-bao-tuong-phan.md` | **Đạt** (Chữ viền đen 3.5px, icon trực quan, tắt hiệu ứng rườm rà, lưu `sessionStorage`, artefact thật đã commit) |
| **AC-P4-04** | Đóng gói phát hành v1.0.0: `contract_version: "1.3"`, README 3 lệnh từ clone sạch, release zip không kèm `.git`, `CHANGELOG.md` theo phase | Clone repo vào thư mục tạm, chạy 3 lệnh README; kiểm tra commit tag | Cần `docs/proof/phase-4/release-v1.0.0.md` | **Chưa đạt** (Chưa nâng manifest lên contract 1.3, chưa gắn tag `phase-4` và tạo GitHub Release v1.0.0) |
| **AC-P4-05** | Mở rộng Leaderboard: lưu top 10 điểm cục bộ, xuất JSON `{"entries":[{name,score,days_completed,seed}]}`, không đổi JSONL | Chạy `day` đủ 5 ngày với cờ `--leaderboard` và `--player-name` | Cần `docs/proof/phase-4/leaderboard.json` | **Chưa đạt** (Chưa triển khai code mở rộng leaderboard) |
| **AC-P4-06** | Hồi quy toàn diện Regression P1–P3: toàn bộ test suite chạy xanh trên commit tag phát hành | `python -m unittest discover -s tests -v` | Cần `docs/proof/phase-4/regression-all.txt` | **Chưa đạt** (Chưa xuất artefact; hiện tại nhánh `main` đạt 191 tests OK, 0 skip khi chạy ngoài sandbox/CI) |

---

## Hiện trạng các mục kiểm chứng

1. **Phần đã hoàn thành và có bằng chứng thật:**
   - **Ticket 03 Phase 4 (Cảnh báo & Tương phản cao - Vinh):**
     - Mã nguồn: `chonoi/web/index.html`.
     - Tài liệu kiểm chứng: [canh-bao-tuong-phan.md](../proof/phase-4/canh-bao-tuong-phan.md).
2. **Phần đang đợi các thành viên phụ trách hoàn tất artefact:**
   - Ticket 01 (`bench_cmd` - Văn Minh): Cần chạy và commit `docs/proof/phase-4/bench.json`.
   - Ticket 02 (`soak_cmd` - Cao Minh): Cần cài đặt `tools/soak.py` và chạy xuất `docs/proof/phase-4/soak.json`.
   - Ticket 04 (Đóng gói Release v1.0.0 - Đức Minh): Cần nâng contract 1.3, tạo zip và Release notes.
   - Phản tư cá nhân: Mỗi thành viên tự viết trong `docs/members/<handle>.md` (hiện có `qvinhh2312.md` và `trandinhnhatminh1452.md`).
