---
name: probe
description: Dựng một ca kiểm để chứng minh hành vi — bằng scenario + inputs rồi đọc JSONL, hoặc bằng mắt trên live UI. Dùng khi cần tái hiện ngạt, hái nút, khách bỏ đi, đóng ca, hoặc kiểm HUD/âm thanh trước khi mở PR.
---

# Probe

## Ca headless

Ba file: `scenario.json`, `inputs.json`, `out.jsonl`.

```json
{"gather": {"player": {"pos": [50, 10], "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": 0},
            "hold": ["bong_sung", "ca_loc"]}}
```

```json
{"frames": [{"tick": 0, "move": [0, 1]}, {"tick": 30, "interact": true}]}
```

```bash
python3 -m chonoi.headless --mode gather --seed 1 --ticks 100 \
  --scenario sc.json --inputs in.json --snapshot-every 1 --out out.jsonl
```

Đọc event:

```bash
python3 -c "import json;[print(r['tick'], r['name'], r['data']) for r in map(json.loads, open('out.jsonl')) if r['type'] == 'event']"
```

Bốn cái bẫy: tick khác giây (60 tick = 1 s, `_s` × 60); event ghi ở `k+1`; hòa khoảng cách theo `id_key` (`N2` trước `N10`); tất định — cùng seed cùng byte.

Ca đáng giữ làm hồi quy thì chuyển thành test trong `tests/` bằng `helpers.run_headless`.

## Ca trên live UI

```bash
python3 -m chonoi.live --mode gather   # hoặc quan, day; --seed N --port N
```

Kiểm 60 giây, mắt và tai:

- Đồng hồ `mm:ss`, đỏ khi còn ≤ 30 s. Oxy đổi màu dưới 25%. Máu hiện đủ tim.
- Prompt hiện đúng chỗ: `[E] Cập bến`, `[E] Hái …`, `[Space] Bắt cá`; giỏ đầy và hồi chiêu có cảnh báo riêng.
- Cảnh báo nguy hiểm: "Thủy quái!" khi Cá Sấu gần, "Hết hơi!" khi oxy cạn. Phím `C` bật tương phản cao — ba cảnh báo vẫn đọc được.
- Âm thanh: phím `M` bật/tắt; nghe được lặn, hái, bắt cá, chuông bếp, tiền.
- `?fx=0` tắt hạt và sóng nước; kiểm lại FPS nếu máy yếu.
- Màn kết thúc: lý do, điểm, nút chơi lại và phím `R`.

## Trước khi mở PR

Chạy `python3 tools/run_checks.py` (xem skill `gate`), chụp ảnh trạng thái đã kiểm vào `docs/proof/phase-<n>/`, rồi mở PR kèm đường dẫn ảnh.
