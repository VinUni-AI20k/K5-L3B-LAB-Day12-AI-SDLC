# JSONL v1.2 — thay đổi

| Mục | Thay đổi |
|---|---|
| snapshot `hold` | mảng cá thể `{id,kind,fresh}` theo thứ tự vào giỏ |
| snapshot `stock` (quán, Shop) | mảng cá thể sắp theo id |
| snapshot `customers[].reserved` | mảng id cá thể |
| event `spoiled` (MỚI) | `{item_id, kind, location: "hold"\|"stock"}`; đúng 1 lần/cá thể; nhiều cùng bước → theo id |
| `cook_started.data.items` | mảng cá thể (fresh lúc nấu) sắp theo kind rồi id; payload món có `base_price` đã chốt |
| `monster_hit.lost`, `faint.lost` | mảng cá thể theo thứ tự bỏ LIFO |
| `gather_end.data.inventory` | schema kho v1.2 |
| `hold_full` | giữ `{kind}` |

Dung sai fresh khi quan sát: ±0.01. Tick của event biên phải chính xác.
Mẫu đề: `{"type":"event","tick":1,"phase":"gather","name":"spoiled","data":{"item_id":"I1","kind":"ca_linh","location":"hold"}}`.
