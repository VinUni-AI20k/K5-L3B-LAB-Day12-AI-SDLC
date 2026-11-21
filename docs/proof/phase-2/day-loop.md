# Phase 2 · Ticket 05 · Vòng ngày, Shop và pause

Kiểm trên cây làm việc với nền `main` tại `6a76767`, Python 3.12.5 trên Windows. Dùng launcher `python3` từ môi trường ảo tạm để chạy cùng `headless_cmd` như manifest.

```powershell
$env:PYTHONPATH = 'tests;.'
$env:PYTHONUTF8 = '1'
python3 -m unittest discover -s tests
python3 -m chonoi.headless --mode day --days 1 --seed 42 --ticks 22200 --snapshot-every 600 --out day.jsonl
```

| Kiểm | Kết quả |
|---|---|
| Suite | 114 test đạt trong 33,564 giây. |
| Một ngày đầy đủ | Chạy 0,505 giây trên máy thực thi. Gather → Quán ở tick 10.800, Quán → Shop ở tick 21.600, Shop tự đóng ở tick 22.200. Kết thúc với `sim_tick: 22200`, `days_completed: 1`, `reason: "days_complete"`. |
| Nhiều ngày và tất định | Fixture rút ngắn hai ca hoàn tất đủ 5 ngày ở tick 3.010. Hai lượt cùng seed và input có JSONL giống từng byte. |
| Shop và pause | Đạt ca mua đúng giá, không đủ tiền, cấp tối đa, lệnh lạ, mua trước khi đóng ở tick cuối và bỏ qua thao tác lúc pause. Test pause giữa lúc nấu xác nhận timer đứng yên và chạy lại ngay ở bước resume. |
| Bàn giao và menu | Bàn giao trong cùng tick, giữ lý do kết thúc pha cũ. Ngất mở Quán với kho rỗng. Kế hoạch lọc món và phần giữ chỗ được kiểm theo kho bàn giao. |
| Smoke hai tiến trình | Kho ghi `{"bong_sung":2,"ca_loc":1}`; snapshot Quán tick 0 đọc đúng. Probe Gather lặp cùng seed cho 44.379 byte giống nhau. |
| Live | Test HTTP đi tới Shop, mua oxy, đóng Shop và nhận trạng thái kết thúc ngày. |

Test hồi quy v1.0 từng coi `attack` là trường lạ. Ở v1.1, `attack` đúng kiểu được đọc và bỏ qua khi mở rộng Lao chưa bật. Test vẫn kiểm `jump` trả mã 2 và thêm ca riêng cho các lệnh v1.1 ngoài pha.
