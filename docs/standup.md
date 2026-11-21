# Standup giữa phase (mỗi người một dòng, 2–3 phút)

## Phase 2

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| 2 | A (NguyenDucNhat3006) | P2-03 cá bơi và sinh theo seed (#25), P2-06 Shop nâng cấp (#26) | AC-P3-02 gather giỏ cá thể; AC-P3-04 bàn giao trong `day` | Hồ sơ cá nhân và phần retro Phase 2 còn thiếu (nhật ký AI đã có ở PR #37) |
| 2 | B (TuHoAnh) | P2-05 quán v1.1: 2 bếp, 4 bàn, 6 món, lọc món theo kế hoạch (#27); retro (#34) | AC-P3-03 quán kho cá thể, giá theo độ tươi | Commit dùng tài khoản `HoAnhTu245`, khác `TEAM.md` (`TuHoAnh`): cần xác nhận |
| 2 | C (Cuongngucuteee) | P2-04 Cá Sấu, Máu (#30); P2-08 menu, pause, HUD, Shop (#35); hồ sơ, nhật ký AI, retro (P2-14) | AC-P3-05 HUD độ tươi; P4-05 đóng gói (nhánh `c/p4-05-packaging`) | Chưa chơi tay trọn một Ngày; Actions chưa bật trên fork nên CI chưa chạy |
| 2 | D (luongvh2510) | P2-01, P2-02 kế hoạch và contract v1.1; P2-07 `day`; P2-09 đến P2-13 smoke, hồi quy, ma trận, retro | Tag `phase-2`; AC-P3-01 schema kho cá thể và contract v1.2 | Giả định `clarify` #6 đến #12 chờ PO; gắn tag cần người dùng đồng ý |

Ghi chú Phase 2 (C, Scrum): tổng hợp từ PR đã gộp, `docs/verification/phase-2.md` và `docs/plan/phase-3.md` lúc 2026-11-21, sau PR #36; mỗi người đọc lại và sửa dòng của mình nếu sai.

## Phase 3

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| 3 | A (NguyenDucNhat3006) | P3-03 độ tươi từng cá thể trong giỏ (#45, đã gộp); P3-05 bàn giao kho cá thể trong `day` (#46, đã gộp) | Gom retro Phase 3 (P3-10); P4-03 bench; demo (P4-10) | Hồ sơ cá nhân còn thiếu |
| 3 | B (TuHoAnh) | P3-04 quán kho cá thể, hao tươi, giá theo độ tươi: đã đẩy nhánh `p3-04-quan-freshness` (commit `a252647`), chưa mở PR | Mở PR P3-04; P4-01 re-planning | Quán v1.2 là phần cuối để bật contract 1.2; HUD độ tươi phía quán chờ P3-04 gộp |
| 3 | C (Cuongngucuteee) | P3-06 HUD độ tươi (#44, đã kiểm với gather v1.2 thật); P4-05 cảnh báo, tương phản cao (#42); làm thay P4-06 đóng gói (#39, đã gộp) | Xem lại HUD phía quán khi P3-04 gộp; chuẩn bị P4-08 | #44 phải gộp sau #42 |
| 3 | D (luongvh2510) | P3-02 kho cá thể, adapter, khối `freshness` (#43, đã gộp) | Smoke bàn giao kho phút 20, bật `contract_version` 1.2, hồi quy, `docs/verification/phase-3.md`, tag `phase-3` | Bật 1.2 còn chờ quán (B); gather (A) đã gộp |

Ghi chú Phase 3 (C, Scrum): tổng hợp từ PR #43 đến #47, nhánh `p3-04-quan-freshness` và `docs/plan/phase-3.md` lúc 2026-11-21 (sau khi #45, #46 gộp); mã việc theo tab Phân công (lệch 1 so với mã AC). Mỗi người đọc lại và sửa dòng của mình nếu sai.

## Phase 4

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| 4 | A (NguyenDucNhat3006) | P4-03 benchmark đã gộp (#52, #56), contract nối `bench_cmd` ở #55. P4-10 đã chạy thử trọn một Ngày bằng phím mô phỏng trong Chrome. | Chơi bản demo trước nhóm, D mở kết quả test và ma trận, B và C trình bày bằng chứng. | Buổi trình bày trực tiếp theo lịch nhóm. |
| 4 | B (TuHoAnh) | **D soạn thay, chờ B xác nhận:** P3-04 quán v1.2 (#49, D mở PR); hồ sơ đặt tên `TuHoAnh.md` | Đọc và sửa dòng retro, nhật ký AI; xác nhận tài khoản commit | Chưa mở PR cho nhánh của mình; tài khoản commit khác `TEAM.md` |
| 4 | C (Cuongngucuteee) | **D soạn thay, chờ C xác nhận:** P4-05 cảnh báo và tương phản cao (#42), P4-06 đóng gói (#39), ghi chép Phase 2 và 3 (#38, #47) | Đọc và sửa dòng retro Phase 4 | Không còn: HUD quán v1.2 và phím H đã có ảnh bằng chứng (`p4-08-hud-quan-v12*.jpg`) |
| 4 | D (luongvh2510) | P4-02 contract 1.3 (#55); P4-04 soak 10 Ngày (#54); P4-07 clone sạch và CI Ubuntu (#57); sửa bench theo Ticket-04 (#56); khung ma trận Phase 4 và release notes (#58) | Điền các ô CHỜ, chạy lại kiểm tại commit gắn tag, file đóng gói, tag `phase-4` và Release `v1.0.0` | Chờ A, B, C nộp hồ sơ, nhật ký AI, retro Phase 4; tag và Release cần người dùng đồng ý |

Ghi chú Phase 4: A và D ghi dòng của mình; dòng của B và C do D soạn thay theo yêu cầu từ lịch sử PR (đánh dấu ở từng dòng), chờ hai bạn đọc và sửa.
