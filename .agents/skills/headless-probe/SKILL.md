---
name: headless-probe
description: Dựng một ca kiểm bằng scenario + inputs rồi đọc JSONL để chứng minh một luật chạy đúng. Dùng khi cần tái hiện một hành vi (ngạt, hái nút, khách bỏ đi, đóng ca) mà không phải chơi tay.
---

# Headless probe

Mọi luật của lab đều kiểm được bằng ba file: `scenario.json`, `inputs.json`, `out.jsonl`.

## Dựng ca

```json
// scenario.json — dựng trạng thái giữa chừng
{"gather": {"player": {"pos": [50, 10], "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": 0},
            "hold": ["bong_sung", "ca_loc"]}}
```

```json
// inputs.json — chỉ khai frame có thay đổi; trường vắng được kế thừa
{"frames": [{"tick": 0, "move": [0, 1]}, {"tick": 30, "interact": true}]}
```

## Chạy

```bash
python3 -m chonoi.headless --mode gather --seed 1 --ticks 100 \
  --scenario scenario.json --inputs inputs.json \
  --snapshot-every 1 --out out.jsonl
```

```bash
# chỉ xem event
python3 -c "import json,sys;[print(r['tick'],r['name'],r['data']) for r in map(json.loads,open('out.jsonl')) if r['type']=='event']"
```

## Bốn cái bẫy

1. **Tick ≠ giây.** Contract ghi `_s` là giây; engine chạy 60 tick/s. `regrow_s: 20` = 1200 tick.
2. **Event ghi ở tick k+1.** Frame tick 0 → event tick 1. Đừng kỳ vọng tick 0.
3. **Hòa khoảng cách theo `id_key`,** không phải so chuỗi: `N2` trước `N10`.
4. **Tất định:** cùng seed + cùng inputs phải ra cùng byte. Nếu khác, ai đó đã dùng `random` toàn cục hoặc đọc đồng hồ hệ thống.

## Đối chiếu nhanh

```bash
python3 -m chonoi.headless ... --out a.jsonl
python3 -m chonoi.headless ... --out b.jsonl
cmp a.jsonl b.jsonl && echo "tất định OK"
```

Khi ca này đáng giữ làm hồi quy: chuyển thành test hộp đen trong `tests/` bằng `helpers.run_headless`.
