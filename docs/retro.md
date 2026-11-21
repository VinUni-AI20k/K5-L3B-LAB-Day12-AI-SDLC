# Retro nhóm

## Phase 2 (nhanh)
> Integrator (NgChiVinh) soạn từ lịch sử git, PR và bằng chứng của phase; cả nhóm sửa/bổ sung ý của mình.

- Điều tốt:
  - Khung v1.1 (contract số chuẩn, nút mới, `--days`) lên `main` sớm (`ac0bdd8`) nên 4 lát làm song song trên cùng nền.
  - `--mode day` + Shop + pause có trước (`2542a39`) → tích hợp sớm; cả 4 lát lõi (cá bơi/sinh, Cá Sấu, 2 bếp/4 bàn/6 món, vòng ngày) vào `main` trước tag, **108/108 test**, 1 Ngày ≈ 0.4 s.
  - Test bắt lỗi thật trước khi tới máy chấm: Shop chưa hiện cấp vừa mua; 2 lỗi lệch 1 tick của Cá Sấu (PR #6) — phát hiện nhờ đọc code theo PRD + dựng scenario, dù `merge-tree` và test cũ đều xanh.
  - QA có smoke tích hợp ở phút 20 (`docs/proof/phase-2/integration.*`) và regression; thêm bằng chứng nhiều Ngày + nâng cấp (`day-multi.md`).
  - Commit của Lâm, Quân, Khoa, Chuẩn đã gắn đúng tài khoản GitHub.
- Điều tệ:
  - Bảng `verification/phase-2.md` chạy ở commit cũ (`d66c50d`, trước Cá Sấu) — suýt gắn tag trên bằng chứng sai; phải chạy lại trên `fe3930f` ngay trước tag.
  - Shop không ai bắt đầu kịp → Integrator viết thay để vòng ngày không bị chặn; kế hoạch phải sửa giữa phase.
  - HUD v1.1 trễ và lỗi (chữ 10–13 px, phím Q/M/Enter không chạy, DayIntro… không hiện) → AC-P2-08 chỉ "một phần" lúc gắn tag.
  - Commit `d66c50d` (cá bơi) lại không gắn tài khoản GitHub (đổi email máy).
  - Một số nhánh tự merge vào `main` không qua kiểm của Integrator; may là test vẫn xanh.
  - Retro, nhật ký AI (thiếu 22520160, truclamld), phản tư cá nhân và 2 mục mở rộng (đang 0/2) dồn về cuối.
- 1 hành động cho Phase 3: **Trước mỗi lần gắn tag, Integrator chạy lại `run-tests`, `smoke-proof`, `hud_check` trên ĐÚNG commit sẽ gắn tag và cập nhật `docs/verification/phase-n.md` từ kết quả đó; mọi lát vào `main` qua PR để Integrator chạy cả bộ test trước khi merge.** — Người nhận: NgChiVinh (Integrator). Kèm theo: bắt đầu 2 mở rộng ngay đầu Phase 3 (`burn` — HoangQuan23112004, `snake` — 22520160).

## Phase 4 (cuối)
> Integrator (NgChiVinh) soạn từ lịch sử git, PR và bằng chứng; điều phối retro truclamld và cả nhóm sửa/bổ sung ý của mình.

- **Rà lại hành động đã chốt ở P2** ("trước mỗi tag, Integrator chạy lại test/smoke/HUD trên ĐÚNG commit gắn tag và
  cập nhật verification; mọi lát vào `main` qua PR"):
  - **Đã làm:** P3 chạy lại bằng chứng trên `0d4676c` sau khi bật v1.2 (thay cho bảng QA cũ "bị chặn"); P4 không dùng
    bằng chứng QA ở `80c8ff4` mà chạy lại trên commit bàn giao `9bb4150` (`docs/proof/phase-4/handoff/`). Tag `phase-4`
    và Release v1.0.0 cùng trỏ `ca3ba6b`. Code của các bạn vào `main`/`v1.2` qua PR #9–#16.
  - **Còn vướng:** vẫn có nhánh tự merge không qua Integrator (PR #8, #15) và push thẳng `main` ở P2 — may là test vẫn
    xanh; lúc gộp, nhánh `chuan` hai lần gây rủi ro (P3 làm mất 5 dòng nhật ký người khác; P4 đổi lệnh contract
    `python3` → `python`). Lý do: chưa bật bảo vệ nhánh `main` và mỗi người chạy trên Windows/Linux khác nhau.
  - **Hành động kèm theo (2 mở rộng):** làm được ở P4 (Cháy món — HoangQuan23112004, Bảng xếp hạng — 22520160),
    chậm hơn kế hoạch (P3) vì lõi v1.2 chiếm hết thời gian.
- **Điều tốt:**
  - Bàn giao đủ 4 phase: `phase-1`…`phase-4`, Release v1.0.0 có gói chạy được; 132/132 test, bench 682 FPS, soak 10/10.
  - Đổi hợp đồng lớn (v1.2 kho cá thể) mà `main` không đỏ lần nào: ADR-0001 + nhánh tích hợp `v1.2` + lớp chuyển
    fixture + CHANGELOG.
  - Test hộp đen bắt lỗi thật trước máy chấm: merge làm mất lát 4 (P1), Shop chưa hiện cấp vừa mua, Cá Sấu lệch 1 tick,
    `avg_fps` không khớp `frames / measured_s`.
  - Công cụ tự viết dùng lại mỗi phase: `smoke_proof.py`, `hud_check.py`, skill `run-tests`/`smoke-proof`.
- **Điều tệ:**
  - Tag `phase-1`, `phase-3` gắn sau mốc giờ.
  - Commit không gắn tài khoản GitHub làm mất công: TrungHieuPh 5 commit + 1 commit "ShipDNX Team", truclamld 1 commit.
  - Việc dồn về Integrator (lõi v1.2, Shop, bench, tích hợp) — một điểm nghẽn; người khác chờ hoặc làm trùng.
  - Ghi chép (phản tư, nhật ký AI, retro) dồn cuối buổi; 2 phản tư thiếu tại commit bàn giao.
- **Số liệu:**
  - Commit có nội dung trên `main` (không tính merge, theo tác giả git): NCV/NgChiVinh 50 · Viet Khoa/khoa-asta 9 ·
    22520160 6 · TrungHieuPh 5 (+1 "ShipDNX Team") · Quan Hoang/HoangQuan23112004 5 · Duc Truc Lam Le/truclamld 4.
    Commit merge/PR: NgChiVinh 17 · khoa-asta 7 · TrungHieuPh 3 · 22520160 3 · HoangQuan23112004 1.
  - Cách đọc code của nhau: Integrator đọc diff + chạy cả bộ test trên bản merge thử trước mỗi PR (#1–#16); QA viết
    test hộp đen theo AC; review chéo qua PR (lát 3 ↔ 4, HUD, Cá Sấu).
  - Token theo người: chưa đo (nhật ký AI ghi "chưa đo"; mỗi người bổ sung từ `/cost` hoặc công cụ của mình nếu có).
- **Một lần AI sai và cách nhóm xác minh:** ở P3, AI (Claude Code, Integrator) ghi trong commit `ff6638d` và nhật ký AI
  rằng cá thể trong giỏ "ươn sau 8400 bước". Khi chạy bằng chứng trên `main` (`docs/proof/phase-3/prd-checks.md`) kết
  quả là bước 8401. Nhóm không sửa code cho khớp con số của AI mà đọc lại luật TICKET-03 ("ươn khi fresh **< 30**"):
  sau 8400 bước fresh mới bằng đúng 30 nên chưa ươn → game đúng, AI tính sai; đã đính chính nhật ký AI. Một lần khác
  cùng P3: lớp chuyển fixture do AI viết đổi luôn fixture cố ý sai `{"ca_loc": -1}` thành hợp lệ, làm test mã 2 báo
  sai — phát hiện vì `test_inv_bad_schema_exit_2` hỏng, sửa để chỉ đổi fixture hợp lệ.
  (Bài học liên quan nhưng không phải lỗi AI: ở P1 `git merge-tree` báo "không conflict" cho nhánh `chuan` dù bản gộp
  đã mất code lát 4 — chỉ chạy cả bộ test trên đúng code nhánh mới thấy, PR #3.)
- **Nếu làm lại, đổi gì:**
  - Bật bảo vệ nhánh `main` (bắt buộc PR + test xanh) từ Phase 1; thống nhất chạy test qua `python3` (WSL/alias) để
    không ai đổi contract cho Windows.
  - Kiểm `git config user.email` của mọi người ngay kickoff (commit gắn tài khoản).
  - Chia lõi lớn (v1.2) theo lát song song ngay phút 0–7 thay vì Integrator làm hết; mỗi người viết phản tư + nhật ký
    AI cuối mỗi phase thay vì cuối buổi.
- **Hành động tiếp theo:** truclamld và 22520160 bổ sung phản tư; TrungHieuPh thêm email vào GitHub; mỗi người điền
  token/chi phí vào nhật ký AI nếu đo được.
