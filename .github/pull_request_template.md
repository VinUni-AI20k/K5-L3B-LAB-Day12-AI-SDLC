## Liên kết
Closes #<số issue nếu có> · Phase: 1 · Module: gather-survival

<!-- Ví dụ module: gather-survival, gather-collection, quan-customer, quan-kitchen, ui, qa. -->

## Tóm tắt

Hoàn thiện cơ chế sinh tồn cho Gather trong `chonoi/sim/gather.py`: phát hiện lặn/nổi,
quản lý oxy, ngạt, mất máu và ngất. Khi nhân vật ngất, giỏ được xóa và ca Gather kết thúc
với lý do `fainted`.

## Tiêu chí chấp nhận đã đạt
- [x] Nhân vật di chuyển và bị giới hạn trong bản đồ.
- [x] Oxy giảm khi ở dưới nước, hồi khi ở mặt nước và được kẹp trong khoảng hợp lệ.
- [x] Phát các event `dive`, `surface`, `oxygen_empty`, `choke`, `faint`.
- [x] Oxy bằng 0 đủ thời gian thì mất máu; hết máu thì ngất và kết thúc Gather.
- [x] Khi ngất, giỏ được làm rỗng và event `gather_end` có reason `fainted`.
- [ ] Giỏ LIFO và giới hạn `hold_capacity` khi nhặt vật phẩm — cần hoàn thiện cùng phần thu thập.
- [ ] Không phá hành vi/contract của phase trước — cần chạy lại smoke test sau khi sửa lỗi `python3` trên Windows.

## Bằng chứng
Lệnh đã chạy và kết quả (dán đầu ra hoặc liên kết đến `docs/proof/...`):

```text
`tests.test_python_starter_units`: Ran 7 tests — OK.

Đã tạo test sinh tồn tại `tests/test_gather_sinh_ton.py`.
Test này chưa chạy được trong môi trường hiện tại vì `game.contract.json` gọi `python3`,
nhưng Windows đang trỏ `python3.exe` tới Windows Store alias và báo `WinError 1920`.
```

## Phần AI hỗ trợ

- Công cụ/agent: Codex.
- Prompt hoặc yêu cầu chính: triển khai phần Người 1 — Gather Survival & Movement.
- Tôi đã tự đọc lại và kiểm tra: `gather.py`, `game.contract.json`, các test sinh tồn
  và diff trước khi chuẩn bị PR.

## Rủi ro / việc chưa làm

* Phần giới hạn giỏ và event `hold_full` chưa hoàn thiện; phụ thuộc logic thu thập của Người 2.
* Smoke test và test sinh tồn chưa thể chạy hoàn chỉnh do lỗi alias `python3` trên Windows.
* Chưa sửa `game.contract.json` vì đây là contract chung của nhóm.

## Checklist người review
- [x] Đúng phạm vi Người 1 và PRD Phase 1.
- [ ] Có test và chạy headless pass — đã ghi rõ lỗi môi trường bên trên.
- [x] Không sửa contract, schema kho hoặc tên event.
- [x] Không hard-code số chuẩn; thông số đọc từ `game.contract.json`.
- [x] PR nhỏ và tập trung vào Gather Survival.
- [ ] Reviewer đã nhận xét trực tiếp trên diff.
