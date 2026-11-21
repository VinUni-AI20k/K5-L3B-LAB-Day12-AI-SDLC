# Ma trận kiểm chứng Phase 3 (`Test Contract v1.2` + Mở rộng `burn`)

| AC | Hạng mục kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| `AC-P3-01` · Kho cá thể `v1.2` | Schema `[{"id","kind","fresh"}]`, số học nguyên `240/đv`, từ chối kho đếm cũ mã `2` | `chonoi/inventory.py`, `tests/test_freshness_gather_v12.py`, `tests/test_smoke_p1.py` | Đạt (`0..24000` round-trip chính xác 100%) |
| `AC-P3-02` · Gather độ tươi | Hàng mới bắt đầu hao ở bước sau `-2/tick`; ngưỡng `fresh=30 -> tick 1` phát `spoiled`; LIFO `lost` là object cá thể | `tests/test_freshness_gather_v12.py`, `tests/test_gather_core_contract.py` | Đạt |
| `AC-P3-03` · Quán độ tươi & giá | Kho thô hao `-1/tick`, phát hết `spoiled` trước tái giữ chỗ 1 lần (ưu tiên `order_tick` rồi `table_id`), `unfulfillable`, `base_price = floor(price * avg_fresh / 100)` + `floor` tip | `tests/test_quan_v12_burn.py`, [spoil.jsonl](../proof/phase-3/spoil.jsonl) | Đạt |
| `AC-P3-04` · Bàn giao kho `v1.2` | Smoke 2 tiến trình `gather -> quan` giữ chính xác id/fresh; chuyển pha `day` không hao thêm tick; Shop không hao | [handover.gather.jsonl](../proof/phase-3/handover.gather.jsonl), [handover.inventory.json](../proof/phase-3/handover.inventory.json), [handover.quan.jsonl](../proof/phase-3/handover.quan.jsonl), `tests/test_quan_v12_burn.py` | Đạt |
| `AC-P3-05` · Mở rộng `burn` | `extensions: ["burn"]`, `burn_s = 20`: tick `1200` vẫn nhặt được, tick `1201` phát `dish_burnt` kèm `order_status` | `tests/test_quan_v12_burn.py`, [burn.jsonl](../proof/phase-3/burn.jsonl) | Đạt |
| `AC-P3-06` · HUD & Hồ sơ nhóm | Hiển thị `%` độ tươi / nhãn `ƯƠN` và thanh đếm cháy; cập nhật ADR, impact matrix, CHANGELOG, clarify, AI log, phản tư TV3 & TV5 | `chonoi/web/index.html`, `CHANGELOG.md`, `docs/members/Besoi2004.md`, `docs/members/letuandat131.md` | Đạt (`check_team.py` OK, toàn bộ suite xanh) |
