# Kiểm chứng P1-04 và P1-05

Kiểm tra trên Windows với Python 3.12.10 trong `.venv`, ngày 2026-11-21.

```powershell
$env:PATH = "$PWD\.venv\Scripts;$env:PATH"
$env:PYTHONPATH = "$PWD\tests;$PWD"
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Kết quả trên bản `main` đã có P1-08: **45/45 test đạt** ở cả commit P1-04 và P1-05. Bộ test gồm smoke test headless, kiểm scenario/contract và máy chủ live.

Đã chạy thêm các kịch bản qua `chonoi.headless` với `--seed 1 --snapshot-every 1`. Các đầu vào và kết quả trung gian dùng thư mục tạm.

| Hạng mục | Kết quả quan sát |
|---|---|
| Lặn, nổi và oxy | `dive` và `oxygen_empty` ở tick 1 khi lặn với 1 oxy. Với 2 máu, `choke` ở tick 60 và 120. Nổi ngay trước nhịp ngạt đặt bộ đếm về 0, giữ nguyên máu và hồi oxy đến đúng mức tối đa. |
| Ngất và cập bến | Ở tick ngất, thứ tự sự kiện là `choke`, `faint`, `gather_end`. File kho là `{"items":{}}`. Khi ngất trùng thao tác cập bến, bắt cá và hết giờ, lượt kết thúc với `fainted`. Khi cập bến trùng hái và hết giờ, lượt kết thúc với `docked`. |
| Hái và mọc lại | Hái `N2` trước `N10` khi cùng khoảng cách, bỏ qua nút chưa mọc lại. Giữ phím không tự hái. Nút hái ở tick 1 mọc lại ở tick 1201. Giỏ giữ thứ tự nhặt. |
| Sức chứa và bắt cá | Nhặt vừa đủ sức chứa thành công. Thiếu chỗ phát `hold_full`, cá và rau vẫn còn. Bắt cá đúng rìa bán kính được, chọn `F2` trước `F10` khi bằng khoảng cách, bắt lại được sau đúng 30 tick. Kiểm tra cả bắt trên mặt nước, bắt ngoài tầm và hái khi đang lặn. |
| Bàn giao sang quán | Hái rau, lặn bắt cá, nổi rồi cập bến tại tick 126. File kho và snapshot đầu của `quan` cùng có `bong_dien_dien: 1` và `ca_linh: 3`. Chạy lại cùng input và seed cho file JSONL và kho giống từng byte. |

Để chạy lại lượt bàn giao, lưu đoạn sau lần lượt thành `scenario.json` và `inputs.json` trong thư mục tạm.

```json
{"gather":{"player":{"pos":[8,0]},"nodes":[{"id":"N1","kind":"bong_dien_dien","pos":[8,0]}],"fish":[{"id":"F1","kind":"ca_linh","pos":[8,2]}]}}
```

```json
{"frames":[{"tick":0,"interact":true},{"tick":1,"move":[0,1],"interact":false},{"tick":31,"move":[0,0],"catch":true},{"tick":32,"move":[0,-1],"catch":false},{"tick":65,"move":[-1,0]},{"tick":125,"interact":true}]}
```

Từ thư mục repo, đặt `$work` là đường dẫn thư mục tạm ở trên rồi chạy các lệnh sau.

```powershell
$python = '.\.venv\Scripts\python.exe'
& $python -m chonoi.headless --mode gather --seed 1 --ticks 600 --snapshot-every 1 --scenario "$work/scenario.json" --inputs "$work/inputs.json" --out "$work/gather.jsonl" --inventory-out "$work/kho.json"
& $python -m chonoi.headless --mode quan --seed 1 --ticks 0 --inventory "$work/kho.json" --out "$work/quan.jsonl"
```

Các giả định chờ PO xác nhận được ghi ở [clarify.md](../../clarify.md).
