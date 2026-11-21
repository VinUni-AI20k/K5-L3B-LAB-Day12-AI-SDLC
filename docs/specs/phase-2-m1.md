# Spec kỹ thuật M1 — Cá Sấu Năm Chèo, Phase 2

[Ticket02, mục 1.2](../../Ticket02.md#L23) · [Bảng công việc](../../phase-2-task.md#L13) · [Test Contract v1.1](../contracts/README.md#L93)

## A. Dev Spec

| Khóa tuning | Giá trị trong preset |
|---|---|
| `tick_hz`, `gather.bounds` | 60 Hz, x ∈ [0,100], d ∈ [0,30] |
| `gather.monsters.spawns` | M1 từ Ngày 1 ([60,24] ↔ [64,24]), M2 từ Ngày 3 ([85,18] ↔ [89,18]) |
| `gather.monsters.species.ca_sau` | `patrol_speed`: 1, `chase_speed`: 3, `detect_radius`: 10, `exit_radius`: 16, `depths`: [10,30], `hit_radius`: 1.5, `recoil_ticks`: 60, `recoil_dist`: 2 |
| `gather.monsters.invuln_ticks`, `loss_ratio` | 90 tick, 0.5 |

1. Khởi tạo từ `spawns` theo Ngày hoặc dùng toàn bộ `scenario.gather.monsters` nếu khai báo, kể cả mảng rỗng. Gather độc lập dùng Ngày 1. Snapshot công bố trạng thái quái theo ID.
2. Giảm bộ đếm bất tử đầu bước. Xử lý bơi, oxy và ngạt trước quái. Nếu ngất do ngạt thì dừng bước.
3. Duyệt quái theo `sort_by_id`. Tuần tra tới waypoint rồi đổi mục tiêu cho bước sau. Vào `chase` khi người chơi đủ sâu và cách không quá bán kính phát hiện. Rời `chase` khi người chơi quá nông hoặc vượt bán kính thoát. Chặn x theo bản đồ và d theo giao của biên bản đồ với dải độ sâu loài.
4. Sau khi cả hai di chuyển, xét một hit nếu người chơi đủ sâu và hết bất tử. Chọn con gần nhất, hòa theo thứ tự ID. Trừ 1 Máu, bỏ `floor(len(hold) × loss_ratio)` món mới nhất trước, đặt bất tử và phát `monster_hit` với `monster_id`, `hp`, `lost`, `pos` của người chơi.
5. Con gây hit bắt đầu `recoil` từ bước sau, đi theo hướng xa người chơi đã chốt lúc chạm (trùng tâm dùng +x). Mỗi bước đi `recoil_dist / recoil_ticks`, kể cả khi bị chặn mép. Khi hết bộ đếm, quay về `patrol`; chỉ xét phát hiện và chạm lại từ bước kế tiếp.
6. Khi hit làm Máu về 0, phát `faint` với `cause: "monster"` và phần giỏ còn lại theo LIFO, rồi `gather_end` với `reason: "fainted"` và kho rỗng. Dừng trước tương tác, bắt cá và hết giờ. Trong `day`, quán vẫn mở với kho rỗng.

Không cần RNG. Giữ hành vi ngạt/ngất Phase 1 và thứ tự hái/bắt hiện có. Scenario cũ dùng bố trí mặc định của bản hợp đồng đang chạy.

## B. Test Spec

Chạy các fixture trong [test_gather_m1_p2.py](../../tests/test_gather_m1_p2.py) bằng `python -m unittest discover -s tests -p "test_gather_m1_p2.py" -v`. Mỗi fixture gọi `headless_cmd` với `--seed 1`, `--snapshot-every 1` và giới hạn tick riêng.

| AC | Fixture | Đối soát JSONL |
|---|---|---|
| P2-M1-01 | Gather mặc định và `day --days 3` với ca ngắn | Snapshot đầu Ngày 1–2 có M1, Ngày 3 có M1 và M2 |
| P2-M1-02 | Người chơi ở đúng biên phát hiện, rồi bơi lên qua độ sâu tối thiểu. Quái ở waypoint trong fixture riêng | `patrol` → `chase` → `patrol`, tốc độ chase, đổi waypoint và bước tuần tra |
| P2-M1-03 | Hai quái trùng tâm với người chơi, ID M10/M2, giỏ 3 món | M2 gây hit trước, rơi đúng một món LIFO, lùi 60 bước, hit tiếp sau 90 tick |
| P2-M1-04 | Người chơi 1 Máu, giỏ 3 món, hết giờ ngay tick bị hit. Lặp trong `day` | `monster_hit` → `faint` → `gather_end`, phần giỏ còn lại mất theo LIFO, file kho rỗng và quán mở với kho rỗng |
