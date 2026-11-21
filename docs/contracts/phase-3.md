# Hợp đồng tích hợp Phase 3 · Test Contract v1.2

Áp dụng Change Request "Mùa Nước Nổi" tại [TICKET-03](../../PHASE-3.md) và phân công tại [Phase 3](../phan-cong.md#phase-3--mùa-nước-nổi--35-phút).

## 1. Schema kho cá thể (v1.2) và chuyển đổi từ v1.1

- **File kho mới (`v1.2`)**: `{"items":[{"id":"I1","kind":"ca_linh","fresh":100},{"id":"I2","kind":"ca_loc","fresh":97.5}]}` (mẫu: [inventory.v12.sample.json](inventory.v12.sample.json)). Kho rỗng là `{"items":[]}`.
- **Ràng buộc cá thể**:
  - `id`: chuỗi khác rỗng, duy nhất toàn bộ kho/lượt. Cấp `I1, I2, ...` tăng liên tục xuyên pha và Ngày, kể cả khi cá thể cũ đã tiêu hoặc mất.
  - `kind`: thuộc `KINDS_P2` (`ca_loc`, `ca_linh`, `ca_keo`, `bong_dien_dien`, `bong_sung`, `keo_neo`).
  - `fresh`: số hữu hạn trong `[0, 100]` (cấm `bool`, `NaN`, `Infinity`).
- **Quyết định tương thích trong lúc chuyển tiếp**:
  - `game.contract.json` giữ `"contract_version": "1.1"` trong lúc các lát TV2–TV4 làm song song để `main` luôn xanh và bộ test P1–P2 vẫn chạy. Khối `tuning.freshness` đã có sẵn từ đầu phase.
  - `read_inventory(path, kinds=KINDS_P2, *, contract_version="1.1")` chọn schema theo `contract_version`: `"1.0"`/`"1.1"` đọc kho đếm, `"1.2"` đọc kho cá thể và trả `BadInput` (mã thoát `2`) cho kho đếm, id trùng, kind lạ, hoặc `fresh` sai.
  - Khi TV2 (`gather`), TV3 (`quan` stock/reserved) và TV4 (`cook`/giá/`day`) tích hợp xong, TV1 bật `"contract_version": "1.2"` trong `game.contract.json` và cập nhật các caller `scenario.py` / sim sang v1.2.

## 2. Giao diện helper bàn giao từ TV1 (`chonoi/inventory.py`, `chonoi/ids.py`)

- `IdAllocator.reserve_all(items, key=lambda x: x["id"])`: giữ toàn bộ ID từ mảng fixture trước khi cấp mới bằng `ids.new("I")`.
- `parse_fresh(value, name="fresh") -> Fraction` và `fresh_to_json(q) -> int | float`: dùng `Fraction` nội bộ. Với `float` trên lưới `1/240` (sai số `<= 1e-11`), khôi phục chính xác `Fraction(n, 240)` qua ghi/đọc file JSON; số thập phân tùy ý dùng `Fraction(str(value))`.
- `validate_item_record(rec, *, kinds=KINDS_P2, seen_ids=None, name="item") -> dict` & `validate_item_list(items, *, kinds=KINDS_P2, seen_ids=None, name="items") -> list[dict]`: kiểm schema `{id, kind, fresh}`, tính duy nhất ID (truyền chung `seen_ids` để kiểm xuyên `hold`/`stock`/`stoves`/`hand`) và bảo toàn thứ tự mảng gốc (dùng cho LIFO).
- `make_item(ids, kind, fresh=100, *, kinds=KINDS_P2, prefix="I") -> dict`: cấp cá thể mới từ `IdAllocator`.
- `decay_items(items, decay_per_s, *, tick_hz=60, spoiled_below=30) -> list[dict]`: giảm tại chỗ (`gather` = `0.5/s` = `2/240` mỗi tick; `quan` = `0.25/s` = `1/240` mỗi tick), kẹp đáy `0`. Trả danh sách cá thể vừa chuyển từ `>= spoiled_below` xuống `< spoiled_below` (so trước làm tròn), đã sắp theo `id_key`. Caller tự gắn `location` (`"hold"`/`"stock"`) và phát sự kiện `spoiled` một lần.
- `is_spoiled(fresh, spoiled_below=30) -> bool`: trả `True` khi `fresh < spoiled_below`.
- `export_items(items, *, kinds=KINDS_P2) -> list[dict]`: chuẩn hóa và sắp theo `id_key` để xuất kho hoặc snapshot `stock`.
- `count_by_kind(items) -> dict[str, int]`: đếm số cá thể theo `kind`.
- `select_freshest(items, kind, count, *, exclude_ids=None, spoiled_below=30) -> list[dict] | None`: chọn `count` cá thể chưa ươn tươi nhất theo `(-fresh, id_key)`, thiếu trả `None`.
- `price_for_items(listed_price, items) -> int` & `tip_for_price(base_price, tip_rate=0.2) -> int`: tính `floor(listed_price * avg_fresh / 100)` và `floor(base_price * tip_rate)`.
- `sort_cook_items(items) -> list[dict]`: sắp `cook_started.data.items` theo `(kind, id_key)`.
- `read_inventory_v12(path, kinds=KINDS_P2)` & `write_inventory_v12(path, items, kinds=KINDS_P2)`: đọc/ghi ép buộc v1.2 (ghi qua file tạm cùng thư mục rồi `os.replace`).

## 3. Thứ tự tích hợp & bảng tác động

| Module / Lát | File chính bị ảnh hưởng | Test giữ / đổi / thêm | Chủ lát |
|---|---|---|---|
| Adapter, ID & Hợp đồng | `game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py`, `chonoi/ids.py`, `chonoi/headless.py`, `chonoi/live.py` | Thêm `tests/test_inventory_v12.py`; giữ test P1–P2 xanh khi đang ở v1.1 | TV1 |
| Gather & mất hàng | `chonoi/sim/gather.py`, `chonoi/scenario.py` (nhánh gather) | Đổi fixture `hold` count → cá thể & `lost` LIFO; thêm test `spoiled` ở tick 1 với `fresh=30` | TV2 |
| Kho quán & giữ chỗ | `chonoi/sim/quan.py`, `chonoi/scenario.py` (nhánh quan) | Đổi fixture `stock`/`reserved` sang cá thể & ID; thêm test `spoiled`, nhả giữ & giữ lại/`unfulfillable` | TV3 |
| Bếp, giá & vòng ngày | `chonoi/sim/quan.py` (`_start_cooking`, `_pay`), `chonoi/sim/day.py`, `chonoi/scenario.py` (day) | Đổi kỳ vọng giá theo `fresh` & ID xuyên ngày; thêm test chốt giá, Shop/pause không hao | TV4 |
| HUD, QA & Release | `chonoi/web/index.html`, `chonoi/live_day.py`, `docs/verification/phase-3.md` | Thêm smoke file/day v1.2, cập nhật regression P1–P2 | TV5 |
