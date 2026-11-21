# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-P1-G2-01 | Unit: cạnh lên, mặt nước, bán kính gồm mép, gần nhất/hòa ID, nút mọc lại và hái cùng tick, `node_yield` theo tuning | [gather-collection-test.txt](../proof/phase-1/gather-collection-test.txt) | Đạt: các test hái cây đều `ok` |
| AC-P1-G2-02 | Unit: chỉ bắt dưới nước, bán kính gồm mép, gần nhất/hòa ID, đủ yield, xóa đàn, cooldown dùng lại ở `t + L` | [gather-collection-test.txt](../proof/phase-1/gather-collection-test.txt) | Đạt: các test bắt cá đều `ok` |
| AC-P1-G2-03 | Unit: giỏ đầy khi hái; cá linh cần 3 ô nhưng giỏ đã có 10/11 ô; không lấy lẻ, không đổi thực thể/cooldown, không thử mục tiêu khác | [gather-collection-test.txt](../proof/phase-1/gather-collection-test.txt) | Đạt: hai test `hold_full` đều `ok` |
| AC-P1-G2-04 | Unit: bến ưu tiên tại mép; hái/bắt ở bước cuối vào kho trước `gather_end`; bến bước cuối có reason `docked` | [gather-collection-test.txt](../proof/phase-1/gather-collection-test.txt) | Đạt: test bến và bước cuối đều `ok` |
| AC-P1-G2-05 | Headless hai tiến trình `gather → quan`; so file kho với event và snapshot quán; `tick_limit` không tạo/ghi đè; test ngất | [Kiểm tra khi ghép](#chạy-lại-khi-ghép-phần-khách-và-kho) | Đạt, gồm test kho rỗng khi ngất |
| PRD-0 D–G, khách và kho quán | Chạy headless với kho mẫu và 6 test về lịch khách, giữ chỗ, hết kiên nhẫn, đóng ca, fixture mâu thuẫn và tính tất định | [Kết quả chạy](../proof/phase-1/quan-customers.md) | 38/38 test hiện có qua. Luồng phục vụ cần chạy lại khi ghép lát bếp. |

## Đánh giá ngắn
- Lượt chạy thật bằng `python -m unittest discover -s tests -v` trên PowerShell: **47 test, 46 đạt, 1 thất bại; `$LASTEXITCODE = 1`**. Trong 15 test Lát 2: 14 đạt, 1 thất bại.
- Test chưa đạt: `test_fainted_clears_hold_before_inventory_written` mong đợi `choke`, `faint`, `gather_end` nhưng thực tế chưa có event nào. Đây là phụ thuộc Lát 1 của Người 1; không sửa/ẩn test để làm xanh.

## Chạy lại khi ghép phần khách và kho

Bộ test trên Windows qua 66/66. Bản ghép bổ sung `faint.data` theo PRD-0 mục E. Test đầu cuối xác nhận đồ rơi theo LIFO, `gather_end.inventory` và file `--inventory-out` cùng bằng `{"items":{}}`. [Test kho khi ngất](../../tests/test_gather_collection.py)
