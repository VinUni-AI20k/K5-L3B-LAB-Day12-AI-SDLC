# Nhật Minh — bằng chứng ticket 03, Phase 1

Ngày: 2026-11-21. Nhánh: `feat/nhat-minh`. Phạm vi: helper hái/bắt cá, test CLI, ghi chép PO.
Nguồn: `docs/specs/phase-1.md`, ticket 03, `docs/contracts/README.md`, các giả định trong `docs/clarify.md`.

**Kết quả cuối: 62/62 test qua trong bản làm việc trên nhánh cá nhân.**
[Log test](nhat-minh-working-tree-tests.txt). Phần luật của Nhật Minh đã nối với core Cao Minh;
chưa có review của người, chưa commit/push/merge trong lượt này.

## Thay đổi

- `chonoi/sim/gather_actions.py`: chọn gần nhất theo khoảng cách Euclid thật, hòa theo `ids.sort_by_id`; giới hạn giỏ; mọc lại; bắt cả đàn và xóa đàn; hồi chiêu. Số lượng, bán kính và thời gian lấy từ tuning, không dùng giá trị dự phòng hard-code.
- `tests/test_gather_actions.py`: 25 test qua `headless_cmd`, đọc JSONL/file kho, không import sim. Có test khoảng cách rất gần nhau để tránh làm tròn trước khi chọn mục tiêu.
- Không sửa contract, schema kho, khung runner, test smoke hoặc `tests/helpers.py`.
- Core của Cao Minh lấy nguyên từ PR #1, commit `9342f9eb0b1e8403eccd595a7459212caf6cf942`: `gather.py`, `tests/test_gather_core.py`, `gather-core.md`. Phần core không phải phần luật mới của Nhật Minh.
- [Patch tích hợp so với core đã merge](gather-actions-integration.patch): import helper, lưu `tuning.tick_hz`, nối hai lời gọi vào đúng thứ tự `step()`. Đã áp dụng trong bản làm việc `feat/nhat-minh` để kiểm chứng phần của mình; Cao Minh cần review phần nối này theo quy ước sở hữu `step()`.
- Không chuyển nhánh, không merge Git và không push. Ref `main` local giữ nguyên `336e0f47ac82fb8818921f073f77237d39520bd3`; không sửa nhánh chung trên GitHub.

## Kết quả thực chạy

| Bản kiểm tra | Kết quả | Log |
|---|---|---|
| Core đã merge `9342f9e`, kiểm ở thư mục tạm | 37/37 qua, exit 0 | [Core](main-9342f9e-tests.txt) |
| Core `9342f9e` + phần Nhật Minh, kiểm ở thư mục tạm | 62/62 qua, exit 0 | [Ghép hai lát](main-9342f9e-with-actions-tests.txt) |
| Bản làm việc thực tế trên `feat/nhat-minh` sau nối helper | **62/62 qua, exit 0** | [Kết quả cuối](nhat-minh-working-tree-tests.txt) |

Lịch sử kiểm chứng: nền cũ có 32 test qua; bổ sung 25 test khi chưa nối helper phát hiện
`FAILED (failures=18, errors=3)` (có subtest). Bản sao nối với starter cũ có 57 test qua
([log cũ](nhat-minh-isolated-tests.txt)). Kết quả cuối ở bảng trên thay thế hạn chế phụ thuộc ticket 02 trước đó.

Lệnh test PowerShell (máy này có `python3`, không cần sửa test helper):

```powershell
$env:PYTHONPATH = 'tests;.'
python3 -m unittest discover -s tests -p test_gather_actions.py -v
python3 -m unittest discover -s tests -v
```

Trên Linux/macOS: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`.

## Đối chiếu AC trong bản làm việc đã nối helper

| AC | Test/bằng chứng | Kết quả |
|---|---|---|
| Bến ưu tiên hơn hái/catch/hết giờ, gồm mép bến dưới nước | `test_dock_precedes_gather_and_time_and_writes_once`, `test_submerged_dock_precedes_catch` | Đạt |
| Hái nút ready gần nhất, hòa ID, chỉ ở mặt nước | `test_gather_nearest_ready_then_numeric_id`, `test_gather_surface_threshold`, các test radius/distance | Đạt |
| Yield, sức chứa, hold_full không đổi nút | `test_gather_exact_capacity_succeeds`, `test_gather_full_preserves_node_and_hold` | Đạt |
| Mọc lại đúng 1200 tick theo preset, hái ngay bước về 0 | `test_regrow_exact_tick_and_gather_in_same_step` | Đạt |
| Bắt cả hai loài, xóa đàn, cooldown 30 tick theo preset | `test_catch_yield_removes_whole_school`, `test_catch_cooldown_boundary` | Đạt |
| Giỏ thiếu chỗ giữ đàn, không thử đàn khác; không có cá không cooldown | `test_catch_full_keeps_school_no_fallback_or_cooldown`, `test_catch_without_fish_is_noop` | Đạt theo giả định Q1 |
| Kho khớp event khi cập bến/hết giờ; hành động tick cuối được giữ | Các test dock và `test_last_tick_action_included_in_saved_inventory` | Đạt; runner hiện ghi một lần sau vòng lặp |
| Tick limit không tạo/ghi đè kho | `test_tick_limit_does_not_create_or_overwrite_inventory` (cả file mới và file có sẵn) | Đạt |
| Ngất ghi kho rỗng, bỏ giỏ LIFO và chặn hành động | `test_choke_starts_59_ticks_after_empty_and_faint_drops_hold_lifo`, `test_faint_precedes_dock_catch_and_timeout` của Cao Minh | Đạt |
| Cùng seed có JSONL giống từng byte; gather → kho → quan | `test_actions_are_deterministic_bytes`, smoke `test_inv_01_gather_writes_inventory_quan_reads_it` | Đạt |

## Bàn giao

Cao Minh review helper và phần nối `step()` trên nhánh của Nhật Minh; Integrator quyết định merge/tag theo quy ước nhóm.
Đã chạy cả test core của Cao Minh lẫn test actions của Nhật Minh trong repo thật; không sửa luật core hoặc test core để làm xanh.
PO xác nhận Q1 với trợ giảng; các câu hỏi khác giữ nguyên trạng thái giả định.
Chưa có người review, chưa commit/push/PR/merge/tag trong lượt làm việc này.
