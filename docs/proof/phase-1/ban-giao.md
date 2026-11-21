# Bằng chứng nghiệm thu Phase 1

Kiểm ngày 2026-11-21 trên Windows PowerShell, Python 3.12.10 và Chrome headless. Bản `main` khi bắt đầu là `fdc986bef0f7aa2636865ccec616f22115c9bbe7`. Bản làm việc khi chạy lại là nhánh `lam` tại `a1e727786f33981ddfbf96876a255a2b364ddec1` cùng các thay đổi bàn giao trong working tree.

## Suite và hai tiến trình headless

```text
python3 tools/phase1.py verify
python3 tools/phase1.py smoke
```

- **Suite** · Bản `main` đầu phiên đạt 45/45. Sau khi bổ sung ba test Quán, bản làm việc đạt 48/48. Kiểm TEAM báo `bomgoa1102`, `lam2121`, `Hungnd1208`, `MN-HD`, khớp `team_size: 4`.
- **Smoke riêng** · 1/1 đạt. Seed 42, Gather bấm E tại bến ở input tick 0 và xuất `{"items":{"bong_sung":2,"ca_loc":1}}`. `gather_end.data.inventory` khớp file. Tiến trình Quán chạy `--ticks 0` nạp `stock` đúng hai mã và số lượng.
- **Gather bước cuối** · Hai fixture headless đều chạy 1 tick với seed 42 và thao tác đúng mép bán kính. Nút vừa mọc lại phát `node_regrown → gather → gather_end` và kho có `bong_sung: 1`. Bắt đàn cá linh phát `fish_caught → gather_end` và kho có `ca_linh: 3`.
- **Ca biên bổ sung** · Ca Quán rút ngắn vẫn đón khách tại `first_customer_tick`. Khách hết kiên nhẫn đúng lúc đóng ca rời với `closing`, uy tín giữ `3.0`. Khách rời lúc còn giờ làm uy tín `2.5`, dọn món trên bếp hoặc tay và giữ giao dịch nguyên liệu đã dùng. Fixture bếp thiếu món/timer, đơn `assigned` thiếu món, hoặc giữ chỗ vượt tồn từ `--inventory` trả 2 và không tạo JSONL.
- **Lý do cập nhật test TEAM** · Ca từ chối mẫu dùng fixture placeholder riêng. File `TEAM.md` thật đã đủ handle và được xác nhận độc lập qua `tools/check_team.py`.
- **Thay đổi khung** · Headless và live chuyển kho đã đọc vào bước kiểm scenario để xác nhận giữ chỗ trước khi dựng phiên. Mã nhóm được cập nhật trong contract. Tuning, phiên bản contract và schema kho v1.0 được giữ nguyên.

## Chrome với mô phỏng trực tiếp

Khởi động `chonoi.live` với seed 42, fixture tại bến và giỏ `ca_loc`, `bong_sung`, `bong_sung`. Chrome headless chọn **Chơi trọn ngày** và thấy HUD oxy. Nhấn E mở màn kết quả và ghi file kho. Chọn **Mở quán** hiển thị HUD kho. Snapshot live đọc `stock: {"bong_sung":2,"ca_loc":1}`.

## Phạm vi bàn giao

GitHub xác nhận fork công khai và bốn PR đã gộp. Tại thời điểm kiểm, `git tag --list phase-1` và `git ls-remote --tags origin refs/tags/phase-1` đều không trả tag. Kết quả chạy lại ở trên gắn với bản làm việc, cần được lưu cùng commit bàn giao trên `main` để gắn tag. [PR #1](https://github.com/lam2121/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/pull/1), [PR #2](https://github.com/lam2121/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/pull/2), [PR #3](https://github.com/lam2121/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/pull/3), [PR #4](https://github.com/lam2121/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/pull/4)
