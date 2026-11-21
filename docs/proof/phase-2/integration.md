# Smoke tích hợp Phase 2 — gather → quán

- Bản kiểm thử: `751da31`.
- Môi trường: Windows PowerShell, Python 3.11.9.
- Seed: 42.

## Fixture và lệnh chạy

`gather-scenario.json`:
```json
{"gather":{"hold":["ca_loc","bong_sung","bong_sung"],"random_fish":false}}
```

`inputs.json`:
```json
{"frames":[{"tick":0,"interact":true}]}
```

Các lệnh dưới đây dùng đường dẫn tới hai fixture trong thư mục tạm:

```powershell
python3 -m chonoi.headless --mode gather --seed 42 --ticks 1 --scenario $scenario --inputs $inputs --inventory-out $inventory --out $gatherOut
python3 -m chonoi.headless --mode quan --seed 42 --ticks 0 --inventory $inventory --out $quanOut
```

## Kết quả baseline

- Cả hai tiến trình thoát với mã 0.
- `gather_end` ở tick 1 có `reason: "docked"` và inventory `{"items":{"bong_sung":2,"ca_loc":1}}`.
- File kho xuất ra khớp inventory của sự kiện.
- Snapshot đầu của quán ở tick 0 có `stock: {"bong_sung":2,"ca_loc":1}`.
- Kết luận: đạt trên `751da31`. Chạy lại trên bản tích hợp Test Contract v1.1 để chốt kết quả bàn giao.

## Kiểm chứng trên nhánh quán Phase 2

- Regression toàn bộ suite trên nhánh quán `2090b6e`: 48/48 đạt trong 10,446 giây, chạy bằng `python3 -m unittest discover -s tests -v` với `PYTHONPATH=tests;.`. Kết quả gồm hai ca QA Phase 1. Ba ca QA Phase 2 trong PR #7 chờ chạy trên bản tích hợp.

- Bản kiểm thử: `origin/codex/quan-phase-2` tại `2090b6e`.
- Môi trường: Windows PowerShell, Python 3.11.9.
- Kết quả: 14/14 test đạt trong 0,901 giây, gồm 12 ca quán và 2 ca bàn giao kho.

```powershell
$env:PYTHONPATH = 'tests;.'
python3 -m unittest -v tests.test_quan tests.test_smoke_p1.Integration.test_inv_01_gather_writes_inventory_quan_reads_it tests.test_smoke_p1.Integration.test_inv_01_not_written_when_tick_limit_first
```

- Snapshot quán có 2 bếp và 4 bàn. Các ca thứ tự nhận đơn, món mới, lọc món theo kế hoạch Ngày trong quán và dọn ca đều đạt.
- Quán đọc đúng kho tại tick 0. Khi gather dừng do giới hạn tick trước khi kết thúc, file kho đích giữ nguyên.
- Kết quả thuộc nhánh quán tại `2090b6e`. Chờ chạy lại trên bản tích hợp Phase 2.

## Kiểm chứng trên main Phase 2

- Ngày kiểm 2026-11-21, Windows PowerShell, Python 3.12.10 và Node.js. Bản vừa pull là `881c4c41413115bc1bc99cc8d76bf7875b86576f`, trùng `refs/heads/main` trên GitHub.
- `git ls-remote origin refs/heads/main refs/tags/phase-2` trả SHA của `main` và chưa có ref `phase-2`. Tag local cũng chưa có. Kết quả dưới đây gắn với SHA đã kiểm.

```powershell
$env:PYTHONPATH = 'tests;.'
$env:PYTHONUTF8 = '1'
python3 -m unittest discover -s tests -v
python3 tools/phase1.py smoke
```

- **Suite tích hợp** · 54 test trong 13,575 giây, 51 đạt và 3 fail. `tests/test_quan.py` đạt 12/12. Các ca hồi quy Phase 1 về fixture sai, ngất do ngạt, kho, snapshot và live đều đạt.
- **Smoke kho** · 1/1 đạt trên `881c4c4`. Cả hai tiến trình thoát 0. Seed 42 ghi `gather_end` ở tick 1, kho `{"items":{"bong_sung":2,"ca_loc":1}}` và Quán nạp đúng ở snapshot tick 0.
- **Tất định** · Chạy hai lần cho mỗi mode bằng `python3 -m chonoi.headless --mode gather --seed 42 --ticks 600 --out gather.jsonl`, rồi đổi `gather` thành `quan` và dùng tên đầu ra riêng. Hai file của cùng mode giống từng byte. Tick 0 có 8 đàn cá, 6 nút rau và 1 Cá Sấu ở Gather, 2 bếp và 4 bàn ở Quán. Cả hai kết thúc với `tick_limit` ở tick 600.

### Các ca chưa đạt

| **Ca kiểm** | **Kết quả tái hiện** | **Điểm cần xử lý** |
|---|---|---|
| `DayShopBoundaries.test_exact_price_purchase_applies_on_next_day` | `--mode day --days 2` trả mã 2 và báo `unrecognized arguments: --days 2`. Chạy riêng `--mode day --seed 42 --ticks 1 --out day.jsonl` cũng trả mã 2 vì `day` chưa hỗ trợ, file JSONL chưa được tạo. | CLI và runner cho `day`, Shop, chuyển pha và nâng cấp ngày kế. |
| `PauseBoundaries.test_gather_pause_freezes_clock_and_resume_steps_immediately` | Trả mã 2, `frame 0 có trường lạ/chưa hỗ trợ: ['pause']`. | Đọc input và cập nhật tick khi pause/resume ở runner. |
| `GatherPhase2.test_monster_hit_drops_half_lifo_and_invulnerability_prevents_repeat` | Trả mã 2, `hold phải là mảng id nguyên liệu hợp lệ`. `gather.hold` kiểm `KINDS_P1` dù kho đọc `KINDS_P2` có `keo_neo`. Fixture đối chứng chỉ đổi `keo_neo` thành `bong_dien_dien` chạy thành công, mất hai món theo LIFO và Máu `3 → 2 → 2`. | Đồng bộ validator giỏ với bộ nguyên liệu v1.1 và chạy lại fixture gốc. |

### UI và live adapter

- Chạy lại `MockSimV11Adapter` trên Node.js với `phase2.preview.json` ở `881c4c4`. Duyệt D1–D5, pause giữ nguyên `phase_tick` khi nhấn tương tác, mua oxy ở Shop Ngày 1, thấy cấp mua 1 và cấp đang dùng 0. Gather Ngày 2 có `oxygen_max_ticks: 2700`. Lần chạy chỉ mua oxy nên tổng kết mẫu là 910k doanh thu, 710k còn lại, uy tín 3,8 và 1210 điểm. Kết quả Chrome cho bố cục và phím nằm trong [bằng chứng UI trên nhánh triển khai](client-ui.md).
- Khởi động `LiveServer` ở localhost, gọi `GET /config` qua HTTP. Manifest là `1.1`, response chỉ chứa `tuning` và chưa công bố `contract_version` hay `capabilities.campaign_v11`. Điều kiện live trong `app.js` chưa thỏa, nên nút **Chơi** đi qua preview. Smoke chuyển kho live một ngày vẫn đạt trong `test_live`.
