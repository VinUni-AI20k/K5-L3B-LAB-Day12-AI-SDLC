# Kế hoạch Phase 1

- **Mục tiêu:** Hoàn thành hai buổi `gather` và `quan` theo Test Contract v1.0, nối bằng file kho; kiểm chứng trên `main` trước tag `phase-1`.
- **Việc / người / phụ thuộc:** Lát 2 — Người 2, Gather: thu thập và bàn giao kho. Phụ thuộc Lát 1 về thứ tự xử lý ngạt/ngất trước tương tác; phối hợp Người 1 vì cùng sửa `chonoi/sim/gather.py`.
- **Rủi ro:** Xung đột khi sửa chung `step()`; test fixture sai miền hợp lệ; xử lý giỏ đầy hoặc bước cuối sai thứ tự; file kho không khớp event `gather_end`.

## Đặc tả kỹ thuật Lát 2 — Người 2: Gather, thu thập & bàn giao kho

### Phạm vi và ranh giới

- Khi triển khai, chỉ điền hai khối `# TODO(nhóm, lát 2)` trong `chonoi/sim/gather.py` và tạo `tests/test_gather_collection.py`. Không sửa khối `# TODO(nhóm, lát 1)` của Người 1: `dive`/`surface`, `oxygen_ticks`, `choke`, `faint`. Không sửa `chonoi/scenario.py`, `chonoi/runner.py`, `chonoi/inventory.py`, `game.contract.json` hay `docs/contracts/`.
- Dùng `self.t` lấy số liệu từ `game.contract.json`, không hard-code số chuẩn trong luật. Dùng `ids.sort_by_id` khi hòa khoảng cách. `interact` và `catch` chỉ tác động ở **cạnh lên**; vị trí xét là sau bước di chuyển. Khoảng cách Euclid tính cả đúng mép bán kính.
- Khung đã giảm `catch_cd_ticks`/`regrow_ticks` ở đầu bước, xét bến trước hái, kết thúc khi hết giờ và ghi kho một lần qua runner. Lát 2 hoàn thiện tương tác và kiểm chứng các phần có sẵn này.

### Phụ thuộc chéo với Lát 1

Khi `faint`, Lát 1 cần lưu `lost = list(reversed(self.hold))`, rồi `self.hold.clear()` **trước** `self._finish("fainted", events)`. Như vậy `gather_end.inventory` và `--inventory-out` đều là `{"items":{}}`; Lát 2 kiểm chứng kết quả, không sửa logic ngất. Bước ngất dừng ngay, không hái/bắt cá hoặc cập bến sau đó.

### Acceptance Criteria

| ID | Điều kiện đạt |
|---|---|
| **AC-P1-G2-01 — Hái cây** | Ở cạnh lên `interact`, nếu `not self._in_dock()` và `self._at_surface()` (`d <= surface_depth`, preset `0.5`), chọn nút `regrow_ticks == 0` gần nhất trong `interact_radius` (preset `2.0m`, tính cả mép); hòa thì ID nhỏ hơn theo `sort_by_id`. Nếu `free >= node_yield` (preset `1`), nối `kind` vào cuối `self.hold`, đặt `regrow_ticks = int(round(regrow_s * 60))` (preset `1200`) và phát `("gather", {"node_id": id, "kind": kind, "amount": 1})`. Nút từ `1` về `0` phát `("node_regrown", {"node_id": id})` đầu bước và có thể được hái ngay cùng bước. |
| **AC-P1-G2-02 — Bắt cá** | Ở cạnh lên `catch`, nếu `catch_cd_ticks == 0` và `not self._at_surface()` (`d > 0.5`), chọn đàn gần nhất trong `catch_radius` (preset `2.0m`, tính cả mép); hòa theo ID nhỏ hơn. Không có cá trong tầm: không event, không cooldown. Nếu `free >= fish_yield[kind]` (preset `ca_linh: 3`, `ca_loc: 1`), nối **đủ** yield vào cuối giỏ, xóa đàn khỏi `self.fish`, đặt `catch_cd_ticks = int(round(catch_cooldown_s * 60))` (preset `30`) và phát `("fish_caught", {"fish_id": id, "kind": kind, "yield": yield})`. |
| **AC-P1-G2-03 — Giỏ đầy** | `free = hold_capacity - len(self.hold)` (preset sức chứa `12`). Nếu `free < required`, từ chối toàn bộ: giữ nguyên giỏ và nút/đàn đã chọn; không đặt cooldown bắt cá và không thử thực thể khác trong tick đó. Phát `("hold_full", {"action": "gather", "node_id": id, "required": 1, "free": 0})` khi giỏ đầy ở preset; hoặc `("hold_full", {"action": "catch", "fish_id": id, "required": yield, "free": free})`. Ví dụ giỏ đã có `10` hoặc `11` ô mà cá linh cần `3` ô thì từ chối. |
| **AC-P1-G2-04 — Bến và bước cuối** | `interact` xét `_in_dock()` **trước** hái; nếu trong bến thì `gather_end` với `docked` và dừng ngay. Khi `time_left_ticks` về `0`, tương tác hợp lệ vẫn được xử lý xong trước `_finish("time", events)`; ở mép bến bước cuối, `docked` ưu tiên `time`. |
| **AC-P1-G2-05 — File kho** | Khi có `gather_end` và `--inventory-out`, file JSON ghi nguyên tử dạng `{"items":{...}}`, bỏ khóa lượng `0`; kho rỗng là `{"items":{}}`. Nội dung khớp `gather_end.inventory`. Nếu chỉ dừng bởi `--ticks` (`tick_limit`), không tạo mới hoặc ghi đè file kho. Hai tiến trình `gather` rồi `quan` dùng đúng cùng file này. |

### Kế hoạch test — `tests/test_gather_collection.py`

- **Unit/từng tick:** cạnh lên chỉ kích hoạt một lần khi giữ nút; bến ưu tiên nút hái; hái đúng mép bán kính, chọn gần nhất và hòa theo ID (`N2` trước `N10`); nút đang hồi không hái được, từ `regrow_ticks: 1` về `0` phát `node_regrown` rồi `gather` cùng tick; kiểm `regrow_ticks` sau hái.
- **Unit/từng tick:** chỉ bắt dưới mặt nước, đúng mép bán kính, chọn gần nhất/hòa ID (`F2` trước `F10`); không cá thì không event/cooldown; bắt đủ yield, xóa đúng đàn; giữ nút không bắt lặp; cooldown chỉ cho bắt lại ở tick `t + L` khi có cạnh lên mới.
- **Unit/từng tick:** giỏ đầy khi hái; giỏ đã có `10` hoặc `11` ô mà cá linh cần `3`; kiểm `hold_full` đúng payload, giỏ/thực thể/cooldown không đổi, không chuyển sang mục tiêu khác. Bước cuối hợp lệ vẫn vào `gather_end.inventory`; trong bến bước cuối kết thúc `docked`.
- **Headless hai tiến trình:** chạy `gather --inventory-out catch.json` để kết thúc, so file với event `gather_end`, sau đó chạy `quan --inventory catch.json --ticks 0` và so `snapshot.stock`. Kiểm `tick_limit` không tạo/ghi đè file; kiểm kho rỗng khi ngất sau khi Lát 1 hoàn thiện.
- **Fixture hợp lệ:** `chonoi/scenario.py` bắt buộc nút cây ở `d == 0`, cá ở `d > surface_depth` (preset `0.5`). Đặt người chơi ngoài bán kính bến khi thử hái, dùng `random_fish: false` hoặc `fish: []` để cô lập tình huống. Chạy toàn bộ test bằng lệnh trong `AGENTS.md`, lưu kết quả thật vào `docs/proof/phase-1/` và dẫn từ `docs/verification/phase-1.md`.
