# Spec kỹ thuật M1 — Độ tươi trong giỏ, Phase 3

[Ticket03](../../Ticket03.md#L14) · [Phân công Phase 3](../../phase-3-task.md#L13)

## A. Dev Spec

`main` tại `238d752` dùng v1.1: `GatherSim.hold` là mảng mã nguyên liệu theo thứ tự nhặt. Các mục dưới đây mô tả hành vi v1.2 để nối vào giỏ cá thể của M2.3 sau khi M6 chốt hợp đồng và adapter.

| Khóa hợp đồng | Giá trị | Vai trò |
|---|---|---|
| `tick_hz` | 60 trên `main` | Số bước mô phỏng mỗi giây |
| `freshness.gather_decay_per_s` | 0.5 theo Ticket03 | Hao tươi trong giỏ |
| `freshness.spoiled_below` | 30 theo Ticket03 | Ngưỡng ươn, so sánh nghiêm ngặt |
| `freshness.initial` | 100 theo Ticket03 | Độ tươi của nguyên liệu vừa nhặt |
| `gather.monsters.loss_ratio` | 0.5 trên `main` | Tỷ lệ số ô rơi khi bị quái đánh |

1. Trong mỗi tick gameplay, sau khi giảm timer và xử lý hồi nút, giảm độ tươi của từng món đã ở trong giỏ đầu tick. Xử lý việc này trước bơi, oxy, ngạt, quái và tương tác. Món vừa hái hoặc bắt bắt đầu hao ở tick gameplay kế tiếp. Runner bỏ qua `GatherSim.step()` khi pause nên giỏ giữ nguyên trong thời gian dừng.
2. Tính `fresh_after = max(0, fresh_before - gather_decay_per_s / tick_hz)`. Dùng biểu diễn chính xác tại biên, thống nhất với adapter và M2. Ví dụ với 240 đơn vị mỗi điểm tươi thì giảm 2 đơn vị mỗi tick, ngưỡng 30 tương ứng 7200 đơn vị. So ngưỡng trước khi định dạng đầu ra.
3. Chỉ phát `spoiled` khi `fresh_before >= spoiled_below` và `fresh_after < spoiled_below`. Payload gồm `item_id`, `kind` và `location: "hold"`. Nếu nhiều món cùng ươn, dùng `sort_by_id` cho thứ tự event. Giữ nguyên thứ tự nhặt trong giỏ. Món ươn vẫn chiếm một ô và vẫn có thể bàn giao.
4. Khi bị quái đánh, bỏ `floor(len(hold) × loss_ratio)` món mới nhất. `monster_hit.data.lost` chứa các cá thể `{id, kind, fresh}` tại thời điểm rơi, sau hao tươi của tick. Nếu hit làm Máu về 0, `faint.data.lost` chứa các cá thể còn lại, mới nhất trước. Ngất do ngạt cũng bỏ toàn bộ giỏ theo LIFO. Giữ thứ tự `choke` hoặc `monster_hit` → `faint` → `gather_end`, với kho rỗng `{"items":[]}` theo v1.2.
5. Bàn giao đúng id, kind và độ tươi hiện có. Trong `day`, không hao thêm vào lúc chuyển pha. Giữ hành vi giỏ mã nguyên liệu và payload của v1.1 khi chạy cấu hình cũ trong quá trình chuyển đổi. M1 không cấp ID và không cần RNG.

## B. Test Spec

[Bộ test M1](../../tests/test_gather_m1_p3.py) bật v1.2 riêng trong tiến trình test khi manifest trên `main` vẫn ở v1.1. Chạy bằng `python -m unittest discover -s tests -p "test_gather_m1_p3.py" -v`. Sau khi bật v1.2 trên `main`, có thể ghi fixture tương ứng vào `scenario.json` và đặt số tick như trong bảng:

```bash
python -m chonoi.headless --mode gather --seed 1 --scenario scenario.json --ticks N --snapshot-every 1 --out gather.jsonl
```

| AC | Fixture | Kết quả mong đợi |
|---|---|---|
| P3-M1-01 | 2 tick, `random_fish:false`, `monsters:[]`, giỏ I10 rồi I2 ở đúng 30, I3 ở 29.99, I4 ở 0 | Tick 1 phát đúng hai `spoiled` theo thứ tự I2, I10. Tick 2 không phát lại. `hold` vẫn đủ bốn món theo thứ tự nhặt, I4 ở 0. |
| P3-M1-02 | 4 tick, I1 ở đúng 30, thêm `--inputs pause.json` với `pause:true` tại frame 0, `false` tại frame 1 và `true` tại frame 2 | Snapshot tick 1–2 giữ fresh 30. Tick 3 resume, `spoiled` xuất hiện ở tick 3 và chỉ một lần. |
| P3-M1-03 | 1 tick, ngoài bến, người chơi trên mặt nước ở vị trí nút đã sẵn sàng, `interact:true` tại frame 0. Lặp với 2 tick | Món bắt đầu ở fresh 100 tại tick nhặt và giảm đúng một bước tại tick 2. |
| P3-M1-04 | 1 tick, người chơi và quái cùng ở [60,24], giỏ theo thứ tự I2, I10, I1, I3 với fresh 100. Thử 2 Máu rồi 1 Máu | `monster_hit.lost` là I3, I1 với fresh sau hao. Với 2 Máu, giỏ còn I2, I10. Với 1 Máu, `faint.lost` là I10, I2 và `gather_end.inventory.items` rỗng. |
| P3-M1-05 | 1 tick, người chơi ở [60,24], `monsters:[]`, 1 Máu, oxy 0, bộ đếm ngạt bằng `choke_interval_ticks - 1`, giỏ I2, I10 ở fresh 30 | Hai event `spoiled` đi trước `choke`. `faint` có `cause:"choke"`, mất I10 rồi I2, sau đó kết thúc với kho rỗng. |

So id, kind, thứ tự mảng và tick event chính xác. So độ tươi trong snapshot và payload với dung sai ±0.01; dùng event để xác nhận nhánh tại ngưỡng 30.
