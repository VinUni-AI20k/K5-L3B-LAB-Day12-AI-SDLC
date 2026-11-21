# Changelog
## Unreleased

### Phase 4 — asset tự tạo (đồ họa SVG + SFX có phụ đề)
- 21 SVG trong `chonoi/web/assets/` sinh bởi `tools/gen_assets.py`; HUD dùng sprite cho Út Sen, cá, Cá Sấu (trước đây HUD chưa vẽ thủy quái), cây nổi, bến, bếp, bàn, khách và món; tự về hình khối cũ nếu asset chưa tải.
- 24 SFX tổng hợp bằng Web Audio (`assets/sfx.js`) kèm phụ đề; phím M tắt/bật tiếng, V ẩn/hiện phụ đề.
- `chonoi/live.py`: thêm route tĩnh `GET /assets/<tên>` (chỉ `.svg`/`.js`, tên phẳng, chặn `..` và `/`); các route `/`, `/state`, `/input`, `/restart` không đổi. Đây là file khung giảng viên nên ghi lại lý do: cần để client nạp được asset.
- `tests/test_assets.py` (12 test). Không đổi luật, tick, sự kiện, JSONL hay `game.contract.json`.
- HUD quán chừa thêm chỗ phía trên cho 3 dòng kho (trước đó bị mép phòng che).

### Phase 3 — đã vào `main` (chạy được cả v1.1 lẫn v1.2; manifest chính còn `"1.1"`)
- Kho cá thể dùng chung `chonoi/items.py`, file kho / scenario / giỏ cá thể, giữ chỗ theo id, hao kho quán, giá theo tươi (lát 0, 3, 4). Bật bằng khối `tuning.freshness`; chưa có khối này thì mọi thứ chạy như v1.1.
- Test hộp đen Phase 3 `tests/test_fresh_p3.py` (28 test) và ma trận `docs/verification/phase-3.md`.
- HUD (`chonoi/web/index.html`) đọc được cả kho đếm (v1.1) lẫn kho cá thể (v1.2): thanh độ tươi, gạch chéo và cảnh báo hàng ươn, kho khả dụng bỏ phần giữ chỗ và hàng ươn.

### Phase 3 — `day` bàn giao kho cá thể (lát 5)
- `day`: chuyển **nguyên mảng cá thể** (id, kind, fresh) từ gather sang quán trong cùng tick, không hao thêm.
- Ngày kế: id mẫu `gather.hold` được cấp **mới** theo thứ tự mảng (kind/fresh ban đầu); id tăng tiếp xuyên pha và Ngày (clarify #19).
- Shop: giữ kho cá thể theo id, hàng thô không hao tươi; kho dư bị bỏ khi Shop đóng.
- `tests/test_day_p2.py` sửa để đúng ở cả v1.1 và v1.2 (fixture qua `mk_hold` / `mk_stock` / `stock_counts` trong `tests/qa_helpers.py`).

### Còn nợ trước khi bật v1.2
- **Gather:** hao tươi giỏ 0.5/s và `spoiled` (6 test QA `@pending`: AC-P3-01, 02, 03, 10).
- **56 test cũ ở 12 file sẽ vỡ khi bật v1.2** (đo bằng suite chạy với manifest v1.2 tạm): `test_quan_lat3` 11, `test_quan_p1` 10, `test_gather_p1` 7,
  `test_quan_lat4` 6, `test_lat2` 5, `test_quan_p2` 4, `test_gather_lat1_p2` 4, `test_gather_lat1` 3, `test_smoke_p1` 2, `test_lat0_v11` 2,
  `test_python_starter_units` 1, `test_p2_lat2_fish` 1. Lý do chung: fixture theo kho đếm. Chi tiết người đổi: `docs/verification/phase-3.md` AC-P3-19.
  Phải sửa **cùng PR** với việc đổi `contract_version` sang `"1.2"` để `main` không đỏ.

### Dự kiến v1.2 — Ticket-03 "Mùa Nước Nổi" (manifest chính chưa bật; bảng dưới là hợp đồng sẽ có hiệu lực khi bật)
**BREAKING — kho đếm theo loại → kho cá thể.** `contract_version` đổi `"1.1"` → `"1.2"`, thêm `tuning.freshness`
`{initial: 100, gather_decay_per_s: 0.5, quan_decay_per_s: 0.25, spoiled_below: 30}`.

| Chỗ | Trước (v1.1) | Sau (v1.2) |
|---|---|---|
| File kho `--inventory` / `--inventory-out` | `{"items": {"ca_loc": 1}}` | `{"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100}]}`; kho rỗng `{"items": []}`; file kho đếm cũ → mã 2 |
| `gather.hold`, `quan.stock` (scenario) | mảng kind / map kind → số | mảng cá thể `{id, kind, fresh}` |
| `customers[].reserved` | map kind → số | mảng id cá thể |
| Giỏ, kho quán trong snapshot | mảng kind / map | mảng cá thể |
| `cook_started.data.items`, `lost` (monster_hit, faint), `gather_end.data.inventory` | mảng kind / map | mảng cá thể |
| Giá món | giá niêm yết | `floor(giá niêm yết × TB fresh các cá thể dùng / 100)`, boa tính trên giá đã chốt |
| Giữ chỗ | theo lượng | theo id: cá thể tươi nhất, hòa id nhỏ; vừa ươn thì nhả hết và thử giữ lại một lần |
| Sự kiện mới | — | `spoiled {item_id, kind, location}` |

**Cách cập nhật fixture:** đổi `"hold": ["ca_loc"]` thành `"hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100}]`; `"stock": {"ca_loc": 1}`
thành mảng cá thể; `"reserved": {"ca_loc": 1}` thành `"reserved": ["I1"]`; file kho cũ phải sinh lại bằng gather v1.2.
Test cũ bị thay bởi luật mới sẽ liệt kê (kèm lý do) ở `docs/verification/phase-3.md` mục AC-P3-19.
