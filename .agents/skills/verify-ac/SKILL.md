---
name: verify-ac
description: Chạy toàn bộ bộ test Phase 1, kiểm tra từng tiêu chí nghiệm thu AC-P1-01..AC-P1-14 và cập nhật trung thực bảng docs/verification/phase-1.md.
---

# Kiểm Chứng & Ma Trận Truy Vết Phase 1 (`verify-ac`)

## Khi nào dùng
- Sau mỗi lần gộp lát vào `main`.
- Ở giai đoạn kiểm chứng bàn giao (phút 45–55) ngay trước khi Integrator gắn tag `phase-1`.

## Quy trình thực hiện

### Bước 1: Chạy bộ test và kiểm danh sách thành viên
- **Linux / macOS:**
  ```bash
  PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
  python3 tools/check_team.py
  ```
- **Windows PowerShell** *(nếu test hộp đen trong `test_smoke_p1.py` cần `python3`, chạy qua WSL/Git Bash để không sửa `game.contract.json`)*:
  ```powershell
  $env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v
  python tools/check_team.py
  ```
- Lưu output thật của `unittest` vào `docs/proof/phase-1/unittest-output.txt` và đảm bảo `check_team.py` báo `OK: 5 thành viên`.

### Bước 2: Đối chiếu `AC-P1-01` .. `AC-P1-14`
| Mã AC | Phạm vi | Nhóm test / Bằng chứng đối chiếu |
|---|---|---|
| `AC-P1-01` | Test Contract v1.0 (`--ticks 0`, tất định, exit 2) | `tests/test_smoke_p1.py` (`Contract`, `ScenarioModes`) |
| `AC-P1-02` | Bơi, tăng/giảm tốc, hướng, chặn biên | `tests/test_smoke_p1.py` (`Movement`) |
| `AC-P1-03` | `dive`/`surface`, oxy mặt/dưới nước, `oxygen_empty` | Test lát 1 (`gather.py`) |
| `AC-P1-04` | Ngạt (`choke` t+59), Máu 0 → `faint` & kho rỗng | Test lát 1 (`gather.py`) |
| `AC-P1-05` | Hái nút mặt nước, `regrow_ticks`, `hold_full` | Test lát 2 (`gather.py`) |
| `AC-P1-06` | Bắt cá dưới nước, `fish_caught`, hồi chiêu, `hold_full` | Test lát 2 (`gather.py`) |
| `AC-P1-07` | Cập bến ưu tiên trước hái (`docked`), hết giờ (`time`) | `tests/test_smoke_p1.py` + test lát 2 |
| `AC-P1-08` | Hợp đồng kho & smoke 2 tiến trình | `tests/test_smoke_p1.py` (`Integration`) + `docs/proof/phase-1/smoke-2proc-log.txt` |
| `AC-P1-09` | Khách theo lịch, chọn món kho khả dụng, giữ chỗ, `no_dish` | Test lát 3 (`tests/test_lat3_khach.py`) |
| `AC-P1-10` | Kiên nhẫn, khách bỏ đi, kiểm mâu thuẫn `scenario.py` | Test lát 3 (`tests/test_lat3_khach.py`) |
| `AC-P1-11` | Tương tác bếp/bàn: nấu, bưng, phục vụ | Test lát 4 (`quan.py`) |
| `AC-P1-12` | Ăn xong trả tiền, boa, uy tín, hết ca `quan_end` | Test lát 4 (`quan.py`) |
| `AC-P1-13` | HUD 2 buổi đọc được khi chơi thử `chonoi.live` | `tests/test_live.py` + chơi thử `chonoi/web/index.html` |
| `AC-P1-14` | DoD: README, `TEAM.md` + `team_size: 5`, 2 skill, log AI, tag | `tools/check_team.py`, `README.md`, `AGENTS.md`, `docs/` |

### Bước 3: Cập nhật `docs/verification/phase-1.md`
- Ghi đủ 14 dòng theo mẫu: `| AC | Cách kiểm chứng | Bằng chứng (link docs/proof/phase-1/...) | Kết quả |`.
- **Nguyên tắc trung thực:** Phần nào chưa merge hoặc test chưa chạy qua thì ghi rõ **Chưa đạt** kèm lý do cụ thể. Không bao giờ sửa `tests/test_smoke_p1.py` cho xanh khi luật sai.
