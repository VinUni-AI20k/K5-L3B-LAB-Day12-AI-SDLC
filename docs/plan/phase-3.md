# Phase 3 — P3-02: Inventory Schema & Day Adapter

**Owner:** Người 2 (`lunaHieu`). **Nguồn:** yêu cầu Test Contract v1.2 trong phân công Phase 3. Repo hiện chưa có tài liệu v1.2 trong `docs/contracts/`; file mẫu ở đó vẫn là schema v1.0. Đường CLI thực tế là `chonoi/headless.py` và `chonoi/live.py` (không có `chonoi/cli.py`).

| AC | Điều kiện đạt |
|---|---|
| AC-P3-I2-01 — ID cá thể | Một `IdRegistry` dùng xuyên các pha/ngày; `next_item_id()` cấp `I1`, `I2`, … tăng đơn điệu. `observe_item_ids()` nhảy qua mọi ID nạp từ scenario/file; ID đã cấp, tiêu hoặc rơi không được dùng lại. |
| AC-P3-I2-02 — Schema | File kho chỉ nhận `{"items":[{"id":"I1","kind":"ca_linh","fresh":100.0}]}`; sáu `kind` chuẩn, ID `I` + số nguyên dương duy nhất, `fresh` hữu hạn trong `[0,100]` và không phải bool. Kho đếm v1.0, trường thiếu/thừa, ID trùng và giá trị sai trả `BadInput`/exit 2. |
| AC-P3-I2-03 — Sao chép & ghi | `clone_items()` không chia sẻ dict con; `save_inventory_atomic()` ghi file tạm cùng thư mục rồi `os.replace`, dọn file tạm nếu lỗi. `tick_limit` không tạo/ghi đè file kho. |
| AC-P3-I2-04 — Scenario & CLI | `gather.hold` và `quan.stock` nhận mảng cá thể, kiểm ID trùng toàn scenario và đồng bộ registry khi dựng sim. `--inventory`/`--inventory-out` dùng schema mảng v1.2; file sai bị từ chối trước khi tạo output. |
| AC-P3-I2-05 — Day adapter | `gather_end.inventory.items` chuyển nguyên `id/kind/fresh` sang Quán ở cùng tick, không hao tươi khi đổi pha. Day mới dùng giỏ mới nhưng cùng registry, nên ID kế tiếp tăng liên tục. Các cấu trúc đếm nội bộ của Quán được adapter từ mảng để giữ logic bếp hiện có cho tới P3-03. |
| AC-P3-I2-06 — Manifest & hồi quy | `contract_version=1.2`; `tuning.inventory` có `gather_decay_per_s=0.5`, `quan_decay_per_s=0.25`, `spoil_threshold=30.0`. Unit/headless kiểm schema, ID, atomic write, bàn giao và toàn suite. |

## Ranh giới tích hợp

- P3-01 sở hữu hao tươi theo tick và luật Gather sâu hơn; P3-02 chỉ khởi tạo/cấp ID và bảo toàn `fresh` ở bàn giao. P3-03 sở hữu chọn cá thể khi nấu và tác động độ tươi tới Quán. Adapter Quán giữ kho đếm nội bộ nhưng snapshot Day và file bàn giao dùng mảng cá thể.
- Fixture Phase 1/2 dạng chuỗi trong `gather.hold` và kho đếm trong `quan.stock` có thể được chuyển đổi **nội bộ** để chạy hồi quy. File `--inventory` không nhận schema cũ. Sau khi P3-01/P3-03 ghép, bỏ adapter cũ nếu không còn test phụ thuộc.
- Vì chưa có tên khóa v1.2 trong `docs/contracts/`, chọn `tuning.inventory.{gather_decay_per_s,quan_decay_per_s,spoil_threshold}`; đối chiếu lại khi nhóm phát hành hợp đồng chính thức.
