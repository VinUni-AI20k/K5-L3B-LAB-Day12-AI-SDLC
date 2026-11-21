# Kiểm chứng P1-12: smoke test và tính tất định của headless

Chạy ngày 2026-11-21 trên Windows (Python 3.13, chỉ có lệnh `python`) ở `main` sau PR #16, sau khi gộp đủ gather (P1-04, P1-05), quán (P1-06, P1-07) và các bài test.
Mọi lệnh gọi `headless_cmd` thật trong `game.contract.json` (hộp đen); không import sim.

## Lệnh

```
python tools/smoke_phase1.py                                    # bảng bên dưới
PYTHONPATH=tests:. python -m unittest discover -s tests         # Ran 157 tests in 11.867s
python tools/check_determinism.py --ticks 3000                  # cả hai chế độ, seed 1
```

## Kết quả `tools/smoke_phase1.py`

```
OK   gather: --ticks 0                                                              mã 0, 2 dòng
OK   gather: ca đầy đủ 10800 tick                                                   mã 0, 0.3s, sự kiện cuối gather_end, end.reason time
OK   gather: tất định seed 1, snapshot-every 1, hai thư mục đầu ra                  b9e56b491dae
OK   gather: tất định seed 1, snapshot-every 10, hai thư mục đầu ra                 d3fe316e0a9d
OK   gather: tất định seed 42, snapshot-every 1, hai thư mục đầu ra                 b9e56b491dae
OK   gather: tất định seed 42, snapshot-every 10, hai thư mục đầu ra                d3fe316e0a9d
OK   gather: tất định seed 2026, snapshot-every 1, hai thư mục đầu ra               b9e56b491dae
OK   gather: tất định seed 2026, snapshot-every 10, hai thư mục đầu ra              d3fe316e0a9d
OK   quan: --ticks 0                                                                mã 0, 2 dòng
OK   quan: ca đầy đủ 10800 tick                                                     mã 0, 0.2s, sự kiện cuối quan_end, end.reason time
OK   quan: tất định seed 1, snapshot-every 1, hai thư mục đầu ra                    c9f8231ad5ab
OK   quan: tất định seed 1, snapshot-every 10, hai thư mục đầu ra                   7db744d9271e
OK   quan: tất định seed 42, snapshot-every 1, hai thư mục đầu ra                   c9f8231ad5ab
OK   quan: tất định seed 42, snapshot-every 10, hai thư mục đầu ra                  7db744d9271e
OK   quan: tất định seed 2026, snapshot-every 1, hai thư mục đầu ra                 c9f8231ad5ab
OK   quan: tất định seed 2026, snapshot-every 10, hai thư mục đầu ra                7db744d9271e
OK   quan có kho và khách ngẫu nhiên: mỗi seed chạy 2 lần giống từng byte (8 seed)  
OK   quan: seed khác nhau cho kết quả khác nhau (ngẫu nhiên thật đi qua Streams)    6 kết quả khác nhau trong 8 seed
OK   bàn giao gather -> quan (PRD-0 mục G)                                          kho {'items': {'bong_sung': 2, 'ca_loc': 1}}, stock tick 0 {'bong_sung': 2, 'ca_loc': 1}
OK   bàn giao: file kho và JSONL quán giống từng byte qua 2 lần                     
OK   chạm --ticks trước khi kết thúc: không tạo file kho                            
OK   đầu vào sai (thiếu --seed) thoát mã 2                                          mã 2
OK   đầu vào sai (--ticks âm) thoát mã 2                                            mã 2
OK   đầu vào sai (--mode day (v1.0)) thoát mã 2                                     mã 2
OK   đầu vào sai (--inventory với gather) thoát mã 2                                mã 2
OK   đầu vào sai (scenario sai khối) thoát mã 2                                     mã 2
OK   đầu vào sai (scenario không tồn tại) thoát mã 2                                mã 2

27/27 mục đạt
```

## Cách đọc

- **Tất định:** mỗi cặp chạy cùng seed, cùng input, cùng `--snapshot-every` cho JSONL giống từng byte (SHA-256 trùng), kể cả khi ghi sang thư mục đầu ra khác. Với gather và quán không kho, kết quả không phụ thuộc seed (Phase 1 chưa có ngẫu nhiên trong các đường này), nên ba seed cho cùng một mã băm là đúng.
- **Đường có ngẫu nhiên thật:** quán có kho đủ và khách ngẫu nhiên chọn món theo seed qua `Streams`. Mỗi seed chạy hai lần giống từng byte, và 8 seed cho nhiều kết quả khác nhau (chứng tỏ seed thật sự được dùng).
- **Bàn giao gather → quán** theo PRD-0 mục G: kho `{"items":{"bong_sung":2,"ca_loc":1}}`, snapshot quán ở tick 0 có đúng `stock` đó; hai lần chạy cho cùng byte kho và JSONL.
- **Mã thoát 2** cho đầu vào sai; chạm `--ticks` trước khi kết thúc không tạo file kho.
- **Hiệu năng:** ca đầy đủ 10800 tick của mỗi chế độ chạy dưới 1 giây.

## Kiểm lại chính bài smoke

Để chắc bài smoke bắt được lỗi, mình cố ý thay lựa chọn món của khách bằng `random.choice` toàn cục (không đi qua `Streams`): mục "mỗi seed chạy 2 lần giống từng byte" chuyển sang LỖI (26/27 đạt). Đã trả `quan.py` về nguyên trạng.

## Chưa kiểm

- Chưa so với bộ test ẩn của giảng viên (không có); chỉ so với Test Contract v1.0 trong PRD-0 mục B, C, E, F, G.
- Chưa chạy trên Linux hoặc macOS; `tools/smoke_phase1.py` chỉ dùng thư viện chuẩn nên chạy lại được.
- Mức cắt của `--snapshot-every` ngoài 1 và 10 chưa thử.
