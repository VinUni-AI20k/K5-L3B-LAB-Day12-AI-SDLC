# Ma trận truy vết Phase 3

Cập nhật 2026-11-21 trên `main` tại commit `330b884` (sau PR #50; gồm P3-01 đến P3-08). Nguồn yêu cầu: Ticket-03 "Mùa Nước Nổi" (khóa theo giờ, nhóm không đọc được bản gốc: tên khóa `freshness` và công thức giá do B đọc từ đề và báo lại, mọi chỗ đoán ở `docs/clarify.md`). Mã AC theo `docs/plan/phase-3.md`; mã việc trên Sheet lệch 1 so với mã AC.
Chạy lại toàn bộ tại commit này: `PYTHONPATH=tests:. python -m unittest discover -s tests` (352 test, OK), `python tools/smoke_phase1.py` (27/27), `python tools/smoke_phase2.py` (15/15), `python tools/smoke_phase3.py` (13/13, contract 1.2 thật), `python tools/check_determinism.py` (gather, quan, day), `python tools/check_no_hardcode.py` (OK). Kết quả ở [p3-07-smoke.md](../proof/phase-3/p3-07-smoke.md).
Cột kết quả ghi trung thực: **đạt**, **đạt một phần** hoặc **chưa đạt**.

## A. Thay đổi phá vỡ: kho cá thể và độ tươi (contract 1.2)

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P3-01 Schema kho cá thể `{id, kind, fresh}`, adapter đếm ↔ cá thể, `contract_version` 1.2 và khối `freshness`, migration test, file kho sai schema thì mã 2 | Test hàm và hộp đen (`v12=True`); phá thử | `tests/test_p3_inventory.py` (27 test), `tests/test_p3_v12_cli.py` (24 test), PR #43, #48, #50; phá thử 9 + 4 + 8 cách, cả hai đợt đầu bắt hết, đợt P3-08 bắt 8/8 | Đạt một phần: tên 4 khóa `freshness` (`initial`, `gather_decay_per_s`, `quan_decay_per_s`, `spoiled_below`) và công thức giá lấy từ lời của B đọc đề, vị trí khối dưới `tuning` là giả định (`clarify` #14, #15) |
| AC-P3-02 Gather: giỏ cá thể, hao 0.5/s, `spoiled` khi xuống dưới 30, `lost` theo cá thể LIFO, `gather_end.inventory` cá thể | Test luật, hộp đen ở tick biên; phá thử | `tests/test_p3_gather.py` (6 test), `tests/test_p3_v12_cli.py`, PR #45; phá thử 9 cách, bắt 8 (lọt: kiểm sức chứa `hold` lúc dựng sim) | Đạt một phần: payload sự kiện `spoiled` (`id, kind, fresh`) và thời điểm hao trong tick là giả định chờ đối chiếu Ticket-03 |
| AC-P3-03 Quán: kho cá thể, hao 0.25/s kể cả hàng đang giữ, giữ chỗ theo id (tươi nhất, hòa theo id), nhả và giữ lại đúng một lần khi ươn, `unfulfillable`, giá `floor(giá × trung bình fresh / 100)` | Test luật; phá thử | `tests/test_p3_quan.py` (5 test), PR #49; phá thử 7 cách, bắt 4 (lọt: `spoiled` phát lại mỗi tick, giữ chỗ chọn cũ nhất, nấu cả hàng ươn; code đúng, test thiếu) | Đạt một phần: test của B chưa đủ chặt; payload `spoiled` của quán (`item_id, kind, location`) khác gather |
| AC-P3-04 `day`: bàn giao cá thể cùng tick, id tăng xuyên pha và Ngày, Shop không hao hàng | Test và hộp đen day 2 Ngày | `tests/test_p3_day_handoff.py` (2 test), `tests/test_p3_v12_cli.py` (day), `tools/smoke_phase3.py`, PR #46; phá thử 5 cách, bắt 4 (lọt: Shop sao chép kho lúc dựng) | Đạt |
| AC-P3-05 HUD hiển thị độ tươi, hàng ươn, đơn bị ảnh hưởng | Test dữ liệu từ snapshot; ảnh chụp; D xem quán v1.2 thật trên trình duyệt | `tests/test_p3_hud_freshness.py` (10 test), [p3-06-hud-freshness.md](../proof/phase-3/p3-06-hud-freshness.md), PR #44; D chạy `chonoi.live --mode quan` với kho cá thể: dòng "Kho ... tươi thấp nhất 19 · ✕ 1 ƯƠN" đúng | Đạt một phần: chưa chơi hết một Ngày với hàng thật hao dần trên trình duyệt |
| AC-P3-06 Smoke bàn giao kho (fresh 100 và fresh 30, hai tiến trình) | Smoke hộp đen | `tools/smoke_phase3.py` 13/13, [p3-07-smoke.md](../proof/phase-3/p3-07-smoke.md) | Đạt |
| AC-P3-07 Hồi quy Phase 1-2, `CHANGELOG.md`, bằng chứng, ma trận, tag | Chạy lại toàn bộ; đọc `CHANGELOG.md` | Số liệu đầu file; `CHANGELOG.md` mục "Phase 3 — contract 1.2" ghi breaking change và lý do mọi test cũ bị đổi | Đạt một phần: tag `phase-3` chưa gắn (cần người dùng đồng ý) |

### Test và công cụ cũ phải đổi và lý do
- `tests/helpers.py` `run_headless` mặc định chạy bản contract 1.1 sinh từ `game.contract.json` (biến `CHONOI_CONTRACT`), vì 27 mục smoke Phase 1, 15 mục Phase 2 và các test luật kho đếm kiểm hành vi không đổi; 1.2 do `tests/test_p3_v12_cli.py` và `tools/smoke_phase3.py` kiểm (`clarify` P3-08).
- `tools/smoke_phase1.py`: thêm `legacy_env` cùng lý do; `tools/smoke_phase2.py` dùng lại.
- `tests/test_contract_v11.py`: khẳng định phiên bản "1.1" thành "1.2", số chuẩn giữ nguyên.
- `tests/test_gather_prd.py`: `invuln_ticks` nhận từ v1.1 trở lên.
- `chonoi/sim/quan.py` (B): điều kiện bật kho cá thể dùng `inventory_schema` để đúng với mọi bản từ 1.2.

## B. Nhóm và quy trình

| Hạng mục | Bằng chứng | Kết quả |
|---|---|---|
| Mỗi người đóng góp Phase 3 bằng tài khoản của mình | D: P3-01, P3-02, P3-02b, P3-07, P3-08 (#43, #48, #50); A: P3-03, P3-05 (#45, #46); B: P3-04 (commit `a252647`, PR #49 do D mở); C: P3-06 (#44) | Đạt một phần: PR của B do D mở và thêm commit tích hợp |
| Nhật ký AI, standup, retro Phase 3 | `docs/ai-usage-log.md` có dòng Phase 3 của C và D (A, B chưa ghi dòng Phase 3); `docs/standup.md` có dòng Phase 3 của cả 4 (C tổng hợp); `docs/retro.md` mục Phase 3 có phần của C và D; phần của A và B do D soạn từ lịch sử PR (P3-10), chờ hai bạn xác nhận | Đạt một phần: A và B chưa ghi nhật ký AI Phase 3, dòng retro của A và B do D soạn thay, chờ hai bạn xác nhận |
| Hồ sơ cá nhân | `docs/members/` có C, B (`TuHoAnh.md`), D | **Chưa đạt** với A |
| Tag `phase-3` | `git tag` | Chưa gắn |

## Đánh giá ngắn

- **Đạt:** kho cá thể và adapter, độ tươi bằng số nguyên (ngưỡng và `floor` đúng từng tick), bàn giao cùng tick trong `day`, headless và scenario theo schema mới (file kho đếm thì mã 2), smoke bàn giao 13/13, hồi quy Phase 1-2 vẫn 27/27 và 15/15.
- **Đạt một phần:** tên khóa và công thức giá (theo lời B, chưa đối chiếu trực tiếp với đề), payload `spoiled` (hai dạng khác nhau), test của quán (B) và gather (A) còn lọt vài cách phá thử, HUD chưa chơi trọn một Ngày, ghi chép của B.
- **Chưa đạt:** hồ sơ cá nhân của A, tag `phase-3`.
- **Hạn chế:** không đọc được Ticket-03 nên mức "đạt" là theo hiểu biết của nhóm; chưa có bộ test ẩn của giảng viên. Luồng phục vụ khách bằng hàng cá thể chỉ được kiểm bằng unit test của B, chưa có ca chơi trọn một Ngày qua CLI.
- **Việc nên làm trước khi gắn `phase-3`:** nhờ B (hoặc ai đọc được đề) đối chiếu tên 4 khóa `freshness`, công thức giá và payload `spoiled` với Ticket-03; A nộp hồ sơ cá nhân và gom retro Phase 3. Đẩy tag cần người dùng đồng ý.
