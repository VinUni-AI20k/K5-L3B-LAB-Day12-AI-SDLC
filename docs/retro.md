# Retro nhóm

## Phase 2 (nhanh) — nháp của Integrator (s0ra1n0), cả nhóm bổ sung / sửa
- **Điều tốt:**
  - Lát 0 (nền v1.1) merge sớm, nên các lát khác code song song trên cùng contract.
  - Mỗi lát có test hộp đen riêng; `verify-phase` gom bằng chứng trong một lệnh.
  - Kết quả cuối phase: 11/12 AC đạt, 179 test xanh, `day` 5 Ngày tất định, 1 Ngày chạy dưới 1 s.
- **Điều tệ:**
  - Lát 0 và lát 5 cùng thêm `--days`/`pause`/`buy`/scenario `day`, nên phải giải 5 file xung đột.
  - Commit cá bơi vào thẳng `main` làm đỏ một test P1.
  - Tốc độ chéo của cá sai √2 lần mà test không bắt được; chỉ lộ ra khi đo trên lần chạy thật.
  - `contract.py` vẫn chặn `burn_s` sau khi nhóm đã chốt bật `burn`.
  - UI Phase 2 (AC-P2-08) chưa làm.
- **1 hành động cho Phase 3:** trước khi merge vào `main`, người merge chạy `python3 tools/run_checks.py` và đo ít nhất một lần chạy thật cho luật có số đo (tốc độ, thời gian).
  - Người nhận: Integrator (s0ra1n0) nhắc trong mỗi PR.

## Phase 4 (cuối) — nháp của PO / điều phối retro (trongnghia2304), cả nhóm bổ sung / sửa

### Rà lại hành động đã chốt ở Phase 2
> "Trước khi merge vào `main`, người merge chạy `python3 tools/run_checks.py` và đo ít nhất một lần chạy thật cho luật có số đo." — người nhận: s0ra1n0.

- **Đã làm (một phần):**
  - PR bật v1.2 (#21) chạy toàn bộ test và smoke bàn giao đúng mẫu Ticket-03 trước khi merge.
  - Lát 3 P3 có kiểm đột biến; `live --mode day` (#28) chơi thử thật và chụp ảnh.
  - Đo thật bắt được lỗi mà test xanh bỏ sót, ví dụ cá bơi chéo nhanh √2 lần.
- **Chưa làm được:**
  - 3 commit đẩy thẳng `main` không qua PR sau tag `phase-2` (`b5379e4`, `759bc60`, `f3148dd`).
  - Riêng `b5379e4` làm `main` đỏ 5 test từ 16:16 tới 16:32, đến khi PR #21 sửa.
- **Vì sao:** hành động phụ thuộc người nhớ, không có ruleset bảo vệ `main` hay CI bắt buộc; sát giờ thì mọi người đẩy thẳng cho nhanh.

### Điều làm tốt
- **Chia việc theo vai cố định qua 4 phase**, mỗi phase có plan, bảng AC và **bảng sở hữu file** (`docs/contracts/README.md`). Nhờ vậy ít xung đột hơn khi 5 người cùng sửa `gather.py` / `quan.py` / `index.html`.
- **Hợp đồng chốt sớm, quyết định ghi lại:** clarify #1–#21, quyết định I-1…I-5 ở contracts.
- **Test hộp đen mạnh:**
  - QA viết test trước theo AC, dùng `@pending` + `QA_STRICT=1`;
  - lát 0 có manifest v1.2 tạm (`CHONOI_CONTRACT`) để thử trước khi bật.
  - Kết quả: 252 test, QA Phase 3 28/28.
- **Mở rộng:** burn (P2, đã khai `extensions`), phụ đề SFX (P4). Asset tự tạo bằng code, không phụ thuộc nguồn ngoài.

### Điều cần sửa
- **Tag trễ hạn** ở Phase 1 và Phase 3, vì không ai giữ đồng hồ mốc tag.
- **Bật v1.2 nửa vời:**
  - Lát 0 đưa code v1.2 vào `main` nhưng manifest vẫn `"1.1"`, nên bên chấm chạy v1.1.
  - Khi bật thì 96 test đỏ; 12 module test còn chạy manifest v1.1 tạm (`tests/legacy_v11.py`).
- **Gộp tự động "êm" nhưng sai:** gộp `gather.py` không báo xung đột mà sinh hai lần hao giỏ.
- **Môi trường Windows:**
  - `python3` thiếu PATH;
  - lỗi in tiếng Việt cp1252;
  - test SVG đỏ vì CRLF.
  - Mỗi lỗi mất thời gian của từng người, không ghi chung sớm.

### Số liệu
- **Commit (không tính merge) theo người:** tiepnnk01-10 34 · trongnghia2304 12 · s0ra1n0 11 · nguyenhung1901 7 · mhoo40 6.
- **PR đã merge:** 26.
- **Cách đọc code của nhau:** người dự phòng trong `TEAM.md` đọc PR của lát kế bên; người gộp kiểm lại sau khi gộp.
- **Token theo người:** ghi trong `docs/ai-usage-log.md`. Đa số dòng còn `…` vì không đo được trong phiên; s0ra1n0 ước ~300k token ở Phase 1.

### Một lần AI sai và cách nhóm xác minh
- **Lỗi:** khi gộp `main` (lát 2 của Vũ) vào nhánh bật v1.2, git gộp `gather.py` **không báo xung đột**. AI coi là xong, nhưng file có **hai** lời gọi hao giỏ (`_tick_hold_freshness` và `_decay_hold`), nên hàng sẽ hao gấp đôi mỗi bước.
- **Xác minh:**
  - grep tên hai hàm sau khi gộp;
  - chạy đúng smoke bàn giao của Ticket-03: `fresh` phải là 99.992 (100 − 0.5/60), không phải 99.983.
- **Lỗi tương tự:** test xanh nhưng cá bơi chéo nhanh √2, chỉ lộ khi đo một lần chạy thật.

### Nếu làm lại, đổi gì — hành động tiếp theo
| Hành động | Người nhận |
|---|---|
| Bật ruleset bảo vệ `main` ngay Phase 1: chỉ merge qua PR, CI `ci / test` phải xanh | s0ra1n0 (Integrator) |
| Đổi phiên bản contract **cùng một PR** với việc chuyển test; không để code mới chạy sau biến môi trường | s0ra1n0 + chủ từng file test |
| Sau mỗi lần gộp: grep hàm trùng + chạy đúng ví dụ / smoke trong ticket, không chỉ chạy test | người gộp (mỗi PR) |
| Một người giữ đồng hồ mốc tag, nhắc trước hạn 10 phút | tiepnnk01-10 (Scrum/Release) |
| Ghi ghi chú môi trường Windows (PATH, `-X utf8`, `.gitattributes` cho SVG) vào `AGENTS.md` ngay khi gặp | người gặp lỗi đầu tiên |
| Chuyển 12 module test còn ghim `legacy_v11` sang kho cá thể | chủ từng file (danh sách ở `CHANGELOG.md`) |
