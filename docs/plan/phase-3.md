# Phase 3 — tác động và tích hợp kho cá thể

Nguồn chuẩn: [PRD Phase 3](../prd/phase-3.md), giao diện chung v1.2 do nhóm thống nhất. Chỉ làm lõi độ tươi; không bật `current` hoặc `reservations`.

## Bảng tác động

| Module | File cần đổi | Test giữ/đổi/thêm | Người phụ trách |
|---|---|---|---|
| Adapter/schema (A) | `game.contract.json`, `chonoi/fresh.py` (mới), `chonoi/inventory.py`, `chonoi/scenario.py`, `chonoi/contract.py`, `chonoi/headless.py`; tài liệu hợp đồng/changelog do tích hợp cập nhật | Giữ kiểm CLI/mã lỗi/tất định; đổi fixture kho đếm sang cá thể; thêm schema v1.2, ngưỡng, round-trip | ToanLee5433; czx04 review |
| Lặn (B) | `chonoi/sim/gather.py`; test gather tương ứng | Giữ oxy/ngạt/bơi/cá/quái/giỏ/bến; đổi hold/lost/inventory; thêm hao tươi, spoiled, id mới và LIFO cá thể | ToanLee5433 |
| Quán (C) | `chonoi/sim/quan.py`, `chonoi/sim/day.py` và phần bàn giao cần thiết ở `chonoi/runner.py`; test quan/day tương ứng | Giữ timer/2 bếp/4 bàn/day_plan/Shop; đổi stock/reserved/cook_started/giá; thêm giữ lại, boa theo giá chốt, id xuyên Ngày | Ishodayo |
| HUD (D) | `chonoi/web/index.html`, phần live cần thiết trong `chonoi/live.py`; test live tương ứng | Giữ input/pause/Shop; đổi hiển thị kho cá thể, thêm độ tươi và nhận diện hàng ươn | itsbra1vo |
| QA (E) | `tests/test_fresh_p3.py` (mới), `docs/plan/phase-3.md` (mới), `docs/clarify.md` | Thêm test hộp đen AC-P3-01–24; giữ nguyên test ngoài lát E để chủ module cập nhật fixture theo PRD | czx04 |

Danh sách trên ghi tác động dự kiến của toàn nhóm, không cấp quyền sửa chéo lát. Nếu hai lát cùng cần file khung, tích hợp viên phân công một người sửa và ghi lý do thay khung theo quy ước nhóm.

## Quyết định schema và thứ tự tích hợp

1. Chuyển thẳng sang `contract_version: "1.2"`; không giữ song song bộ đọc v1.1. File kho đếm trả mã 2. Fixture cũ chuyển thành mảng `{id,kind,fresh}`, `reserved` thành mảng id. Các test luật còn hiệu lực phải tiếp tục chạy, chỉ đổi kỳ vọng khi PRD ghi thay thế.
2. Ghép A trước để chốt `fresh.py`, tuning và adapter. Trên nền A, ghép B, C, D song song theo chữ ký chung; E kiểm bản hợp nhất sau đó. Mỗi worktree chưa ghép có thể đỏ vì thiếu phụ thuộc; không skip hay thay luật test để xanh.
3. Trên nhánh tích hợp, chạy smoke kho hai tiến trình **trước khi lên main**: gather fixture fresh 100, interact frame 0, ghi kho; quan đọc file với ticks 0; đối chiếu id/kind/fresh với file và `gather_end`. Kiểm thêm bàn giao day cùng tick và id xuyên Ngày.
4. Chạy regression P1–P2 còn hiệu lực cùng bộ P3, review thay đổi rồi mới gộp main/tag theo quy trình nhóm. Các smoke cũ dùng kho đếm phải được chủ module cập nhật schema trước khi dùng làm bằng chứng v1.2.

Lệnh kiểm:

```sh
PYTHONPATH=tests:. python3 -m unittest test_fresh_p3 -v
PYTHONPATH=tests:. python3 -m unittest discover -s tests 2>&1 | tail -30
tools/smoke_p1.sh
tools/smoke_p2.sh
```

## Ánh xạ test QA

Tên `test_ac_p3_XX_*` là mã QA cục bộ (PRD không phát hành danh sách AC đánh số), để nối vào ma trận verification của tích hợp viên:

- 01–03: contract v1.2, fixture spoiled tick 1 đúng payload, smoke gather → file → quan.
- 04–09: từ chối kho đếm/schema/kind/id/fresh sai, chấp nhận kho rỗng.
- 10–13: tốc độ hao hai pha, kho giữ chỗ vẫn hao, spoiled một lần theo id, ngưỡng trước làm tròn và đáy 0.
- 14–17: giữ theo id/tươi nhất/hòa id số, tiêu đúng phần giữ, giữ lại khi ươn và unfulfillable.
- 18–19: thứ tự cook_started `(kind,id)`, trung bình độ tươi và floor, giá chốt đi xuyên nấu/bưng/giao/trả tiền, boa trên giá chốt.
- 20–21: day bàn giao cùng tick không hao thêm, cấp id xuyên Ngày, pause/resume dừng/tiếp hao.
- 22–24: nhả toàn bộ công thức, ưu tiên bàn khi giữ lại, từ chối phần giữ sai/mâu thuẫn.

Test chỉ chạy `run_headless`, đọc JSONL/file; không gọi sim hay tạo bản `fresh.py` giả. Số liệu luật lấy từ `game.contract.json`; thiếu `tuning.freshness` là assertion rõ ràng, không phải lý do bỏ qua test. Test fresh 30 của PRD được dựng bằng `spoiled_below` trong contract; không ghi đè dữ liệu tuning ở test.

## Điểm cần kiểm sau ghép

- Bản nền Phase 2 hiện là v1.1, chưa có `chonoi/fresh.py`; các test P3 chưa thể xác nhận luật v1.2 trước khi ghép A–D.
- Snapshot Shop phải xuất stock cá thể; Shop mua nguyên liệu nếu có ở bản nền cần id mới và fresh 100 Ngày kế. Bộ QA này không tự đặt tên lệnh mua hàng ngoài contract hiện có (chỉ có nâng cấp oxygen/hp).
- Chữ ký `read_inventory(path, tuning)`, `inventory_items()` và chuẩn hóa scenario phải thống nhất; id không được dùng lại sau khi nguyên liệu bị tiêu/bỏ. Các test seed/tất định, ghi nguyên tử, mất hàng và HUD cũ cần chủ module cập nhật rồi chạy trên bản ghép.
- Lát E không sửa `AGENTS.md`, changelog, verification, proof, ai-log hay retro vì ngoài phạm vi file được giao; tích hợp viên chịu trách nhiệm các mục DoD đó.

## Kết quả trên worktree lát E (2026-11-21, chưa ghép A–D)

- `PYTHONPATH=tests:. python3 -m unittest test_fresh_p3 -v`: 24 test, 5 pass, 19 fail, 0 error, 0 skip. Nền còn contract 1.1/thiếu freshness/chưa nhận kho cá thể; chưa xác minh được hành vi P3. Năm test âm pass trên bộ đọc cũ chưa chứng minh bộ đọc v1.2 đúng.
- `PYTHONPATH=tests:. python3 -m unittest discover -s tests 2>&1 | tail -30`: 187 test, 167 pass, 19 fail P3 và 1 error ngoài lát E ở `test_live.LiveServerTest.test_state_input_and_clean_stop`. Lỗi `PermissionError: [Errno 1] Operation not permitted` khi bind socket HTTP trong sandbox; không sửa file live/test_live.
- `git diff --check`: đạt. Không tạo bản `fresh.py` thay thế, không commit/push. Chỉ thay ba file thuộc lát E; thư mục `docs/prd/` đã untracked từ trước khi làm.
