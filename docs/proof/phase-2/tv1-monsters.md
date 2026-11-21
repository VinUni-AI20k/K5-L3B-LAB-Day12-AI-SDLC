# TV1 · Cá Sấu, Máu và ngất · Phase 2

## Phạm vi đã kiểm chứng

Ngày kiểm chứng 2026-11-21. Chạy bằng Python tại workspace trên Windows. Toàn bộ suite đạt 70/70 test. Bộ test TV1 mới có 9 test, gồm fixture headless và kiểm tra trực tiếp khởi tạo theo ngày. Kết quả này áp dụng cho cây làm việc hiện tại, chờ gắn commit bàn giao.

| Yêu cầu TICKET-02 | Bằng chứng |
|---|---|
| Một hit mỗi bước, hòa theo ID số, giỏ lẻ rơi floor(n/2) theo LIFO | test_hit_tie_lifo_and_recoil |
| Recoil 60 bước sau hit, trùng tâm dùng +x, lùi 2 m, bước cuối chưa được hit | test_hit_tie_lifo_and_recoil |
| Máu về 0 do quái, faint bỏ phần còn lại, xuất kho rỗng, ưu tiên trước hết giờ | test_monster_faint_loses_remainder_and_saves_empty_stock |
| Ngạt xuyên bất tử, giữ hàng nếu chưa ngất | test_choke_ignores_invulnerability_and_keeps_hold |
| Cùng bước xử lý ngạt trước hit | test_choke_precedes_hit_in_same_step |
| Bất tử giảm trước hit | test_invulnerability_expires_before_hit |
| Patrol tới waypoint rồi đổi mục tiêu, ra vùng sâu thì thoát chase | test_patrol_arrival_and_chase_exit |
| Recoil chặn biên map và độ sâu | test_recoil_clamps_map_and_depth |
| M1 D1–D2, thêm M2 D3, fixture [] thay toàn bộ | test_default_spawns_by_day_and_empty_override |
| Fixture mâu thuẫn trả mã 2 | test_bad_monster_fixtures_exit_2 |

Lệnh kiểm lại là `python -m unittest discover -s tests -v`. [Bộ test TV1](../../../tests/test_gather_monsters.py)

## Bàn giao tích hợp

Đã chạy riêng `python -m unittest discover -s tests -p test_smoke_p1.py -v`, kết quả 20/20 đạt. Bộ công khai bao gồm CLI, lỗi đầu vào, JSONL tất định, chuyển kho hai tiến trình, giới hạn tick và chuyển động. [Log smoke v1.0](contract-v1.0.log). Kết quả bộ công khai chưa bao phủ toàn bộ các yêu cầu DoD hoặc test ẩn.

TV4 truyền `day=N` vào GatherSim khi dựng mỗi ngày. Tham số mặc định 1 cho gather độc lập. TV4 áp tuning oxy/Máu hiệu lực của ngày trước khi dựng sim, để oxygen_max và hp_max trong snapshot đúng cấp.

TV5 đọc monsters[] gồm id, kind, pos, waypoints, target_idx, state, state_ticks_left, recoil_dir và player.invuln_ticks để vẽ cảnh báo. TV2 ghép cá bơi/sinh sau tương tác, catch và xét hết giờ trong GatherSim.step.

Chưa kiểm chứng luồng ngất → mở quán bằng --mode day hoặc cấp oxy/Máu qua Shop, vì bản hiện tại còn CLI/manifest v1.0. Khối tuning.gather.monsters đã thêm theo v1.1. TV4 chịu trách nhiệm nâng contract_version khi ghép đủ cấu hình. Phần chơi trực tiếp và HUD quái cần TV5 kiểm tra sau tích hợp.

## Review và tích hợp PR #8

Đã ghép main có cá bơi/sinh của TV2 vào nhánh TV1, giữ cả cấu hình cá và quái. Bộ test tích hợp đạt 75/75. Manifest sau tích hợp theo main là v1.1. Review bổ sung kiểm tra kind sai kiểu để fixture monsters trả mã 2 thay vì lỗi thực thi. Luồng day/Shop và HUD vẫn cần chủ lát kiểm chứng khi tích hợp.
