# Bằng chứng QA Phase 1

- Người kiểm thử: Đặng Nguyễn Nhật Minh (`MN-HD`).
- Môi trường: Windows PowerShell, Python 3.11.9.
- Test QA: `tests/test_qa_phase1.py`, commit `6157804` và `7a3292b`.

## Lệnh chạy

```powershell
$env:PYTHONPATH = 'tests;.'
python3 -m unittest discover -s tests -v
```

## Kết quả

| Bản kiểm thử | Kết quả | Ghi chú |
|---|---|---|
| Nhánh QA `7a3292b`, đã chứa `main` tại `e08a53f` | 42/43 đạt | Ca ngất ở tick biên chưa đạt. Tick 1 chỉ có snapshot. |
| Nhánh gather `origin/NTD` tại `cecbe8e`, chép thêm file test QA từ `7a3292b` vào worktree | 43/43 đạt | Cả hai ca QA và smoke chuyển kho gather → quán đều đạt. |

- **Ngất ở tick biên:** Trên `cecbe8e`, tick 1 có `choke → faint → gather_end → snapshot`. Giỏ rơi theo LIFO và file kho xuất ra rỗng, khớp payload của `gather_end`.
- **Fixture sai:** `player.hp=0` trả mã thoát 2 và giữ nguyên từng byte của hai file đầu ra đã có.
- **Chuyển kho gather → quán:** Smoke seed 42 đạt. Snapshot quán tick 0 đọc đúng `{"bong_sung":2,"ca_loc":1}`.
- **Chờ xác nhận:** Chạy lại suite trên bản tích hợp có cả gather và test QA trước khi chốt ma trận Phase 1.