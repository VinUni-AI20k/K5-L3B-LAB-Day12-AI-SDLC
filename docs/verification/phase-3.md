# Ma trận kiểm chứng Phase 3

Cập nhật trên `main` tại commit `0d4676c` (sau PR #11 bật Contract v1.2; ngay trước commit gắn tag `phase-3` —
commit gắn tag chỉ thêm bằng chứng, file này và nhật ký). AC-P3-01 → 07 do khoa-asta đặt và kiểm trên nhánh `v1.2`;
toàn bộ chạy lại trên `main` theo hành động retro Phase 2.

| AC | Kiểm chứng / bằng chứng | Trạng thái |
|---|---|---|
| AC-P3-01 | Kho đếm v1.1 và kho cá thể sai (fresh 101, id trùng, kind lạ) → mã 2: `tests/test_smoke_p1.py::Integration.test_inv_bad_schema_exit_2`; [prd-checks.md](../proof/phase-3/prd-checks.md) | đạt |
| AC-P3-02 | Fixture ngưỡng của PRD (fresh 30, 1 bước) → đúng dòng `spoiled` mẫu ở tick 1, đúng một lần: `tests/test_qa_phase3.py`, `tests/test_gather_freshness_p3.py`; [prd-checks.md](../proof/phase-3/prd-checks.md) | đạt |
| AC-P3-03 | Phần giữ có cá thể vừa ươn → nhả, giữ lại một lần bằng id khác / thiếu → `unfulfillable`: `tests/test_qa_phase3.py::Phase3FreshnessQA.test_spoiled_reserved_item_releases_and_reholds_order_once`, `tests/test_p3_quan_fresh_burn.py` | đạt |
| AC-P3-04 | Giá = floor(niêm yết × fresh TB / 100), boa trên giá đã chốt: `tests/test_qa_phase3.py::…test_cook_price_floors_after_freshness_adjustment`, `tests/test_quan_lat4.py`, `tests/test_p2_quan_shop.py` | đạt |
| AC-P3-05 | Smoke bàn giao file `gather --inventory-out` → `quan --inventory`: id/kind khớp, fresh hao đúng 1 bước, quán nhận đúng id/kind/fresh: [smoke.md](../proof/phase-3/smoke.md) (7/7, `0d4676c`); bản QA trên `v1.2`: [qa-results.md](../proof/phase-3/qa-results.md) | đạt |
| AC-P3-06 | Day: bàn giao cùng tick không hao thêm; Ngày 2 cấp id mới cho mẫu `gather.hold`; ươn trong giỏ ở bước 8401 (8400 bước tới đúng 30, chưa ươn): [prd-checks.md](../proof/phase-3/prd-checks.md), `tests/test_qa_phase3.py::…test_day_handoff_preserves_gather_freshness_in_same_tick` | đạt |
| AC-P3-07 | Regression P1–P3 toàn nhóm trên `main`: [regression-main.txt](../proof/phase-3/regression-main.txt) **121/121 OK** (`0d4676c`). Test P1–P2 đổi vì luật [THAY THẾ] đều ghi lý do (CHANGELOG mục "Cách cập nhật fixture", `tests/helpers.py`) | đạt |
| AC-P3-08 | Thay cho dòng "chặn" trước đó (112 test, 12 fail, 5 lỗi trên `v1.2` trước khi tích hợp PR #9, #10 và `test_quan_lat3`) — xem AC-P3-07 | đạt (đã gỡ chặn) |
| AC-P3-09 | HUD đọc được độ tươi / nhận ra hàng ươn (thanh độ tươi, PR #10): [hud.md](../proof/phase-3/hud.md) **67/67** trên `0d4676c` (gồm chữ ≥ 18 px ở 1280 px) | đạt (tự động; chưa ghi chơi tay) |

## Ghi tác động, schema và thứ tự tích hợp
- [ADR-0001](../adr/0001-kho-ca-the-do-tuoi.md): quyết định schema, bảng tác động (module / file / test / người), thứ tự tích hợp qua nhánh `v1.2` để `main` luôn chạy được.
- [CHANGELOG.md](../../CHANGELOG.md): breaking change kho cá thể, cách đổi fixture. Hợp đồng nhóm [`docs/contracts/README.md`](../contracts/README.md) đã sang v1.2 (`docs/clarify.md` #19).

## Đánh giá ngắn
- Đạt: AC-P3-01 → 09 trên `main` `0d4676c`.
- Chưa làm / ghi trung thực: **mở rộng** — mã Cháy món (`burn`) có trong `quan.py` và test của HoangQuan23112004 nhưng **chưa bật** trong manifest (`extensions: []`, `burn_s: null`), nên chưa tính là mục mở rộng; nhóm 6 người còn 0/2 mục cho cả lab. Tag `phase-3` gắn sau mốc 2:30.
- Điều cần chỉnh cho Phase 4: bật và kiểm 2 mở rộng (`burn`, `snake`) với bằng chứng; mọi lát vào nhánh tích hợp qua PR (lần này nhánh `chuan` gộp `main` làm mất 5 dòng nhật ký của người khác — không merge, chỉ cherry-pick).

## Bổ sung sau tag `phase-3`
- PR #12 (22520160, `8107bbb`): `tests/test_quan_lat3.py` viết lại theo v1.2 bằng `items()` và thêm
  `test_spoiled_reserved_item_is_released_and_rereserved_once_by_id` (cá thể giữ chỗ vừa ươn → `spoiled` → giữ lại
  bằng cá thể tươi nhất, bước sau không đổi) — củng cố AC-P3-03. Trên `main` `65b5406`: **122/122 OK**. Không nằm
  trong tag `phase-3` (merge sau mốc).
