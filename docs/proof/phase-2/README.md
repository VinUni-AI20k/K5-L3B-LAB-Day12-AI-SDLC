# Bằng chứng Phase 2

Sinh bằng `python3 tools/proof_p2.py` ở commit **`3edd7e0`**, lúc 2026-11-21 12:52. (Chưa có tag `phase-2` lúc sinh.)

| Kiểm chứng | File | Kết quả |
|---|---|---|
| Toàn bộ test (`unittest discover -s tests -v`) | [`tests-full.txt`](tests-full.txt) | Ran 156 tests in 11.101s · OK |
| Đầu ca seed 1: 8 đàn ở điểm sinh khác nhau | [`fish/gather.jsonl.txt`](fish/gather.jsonl.txt) | F1 ca_loc [30.0, 10.0], F2 ca_linh [15.0, 5.0], F3 ca_loc [15.0, 10.0], F4 ca_linh [45.0, 10.0], F5 ca_loc [60.0, 10.0], F6 ca_loc [75.0, 16.0], F7 ca_loc [45.0, 16.0], F8 ca_keo [45.0, 24.0] → ĐẠT |
| Sinh theo lịch mỗi 360 tick, trần 12 | `fish/gather.jsonl.txt` | t360 F9 ca_loc, t720 F10 ca_linh, t1080 F11 ca_linh, t1440 F12 ca_linh; cuối ca 12 đàn → ĐẠT |
| Cá bơi trong x ∈ [4, 96] và dải độ sâu loài (181 snapshot) | `fish/gather.jsonl.txt` | ĐẠT; tuổi F1 cuối ca `age_ticks` = 10799 |
| Tất định ca sáng (chạy lại seed 1) | `fish/gather-rerun.jsonl.txt` | sha256 e7a7d89a5307… = e7a7d89a5307… → GIỐNG TỪNG BYTE |
| Cá Sấu chạm: mất floor(n × 0.5) hàng LIFO, bất tử 90 tick | [`monsters/hit.jsonl.txt`](monsters/hit.jsonl.txt) | t1 hp 2 mất ['bong_sung', 'ca_linh'], t91 hp 1 mất ['bong_sung'], t181 hp 0 mất []; khoảng cách giữa các lần chạm [90, 90] → ĐẠT |
| Ngất do Cá Sấu (hp 1) | [`monsters/faint.jsonl.txt`](monsters/faint.jsonl.txt) | [(1, 'monster_hit'), (1, 'faint'), (1, 'gather_end')]; faint `{"cause": "monster", "lost": ["bong_sung", "ca_loc"], "hp": 0}`; kho `{"items": {}}` → ĐẠT |
| Mode day 3 Ngày (gather → quan → shop) | [`day/day.jsonl.txt`](day/day.jsonl.txt) | t0 N1 day_start, t0 N1 phase_start(gather), t10800 N1 gather_end, t10800 N1 phase_start(quan), t21600 N1 quan_end, t21600 N1 phase_start(shop), t22200 N1 shop_end, t22200 N2 day_start, t22200 N2 phase_start(gather), t33000 N2 gather_end, t33000 N2 phase_start(quan), t43800 N2 quan_end, t43800 N2 phase_start(shop), t44400 N2 shop_end, t44400 N3 day_start, t44400 N3 phase_start(gather), t55200 N3 gather_end, t55200 N3 phase_start(quan), t66000 N3 quan_end, t66000 N3 phase_start(shop), t66600 N3 shop_end; end `days_complete`, days_completed 3 → ĐẠT |
| Cá Sấu theo Ngày trong mode day (`from_day`) | `day/day.jsonl.txt` | thấy {1: ['M1'], 2: ['M1'], 3: ['M1']}, contract mong {1: ['M1'], 2: ['M1'], 3: ['M1', 'M2']} → CHƯA ĐẠT (chờ `day.py` truyền `GatherSim(..., day=self.day)`) |
| Tất định mode day (chạy lại seed 1) | `day/day-rerun.jsonl.txt` | sha256 43df893c65b2… = 43df893c65b2… → GIỐNG TỪNG BYTE |
| `--days` sai → mã 2, không ghi đầu ra | — | `--mode day --days 0` → 2 (đầu vào sai: --days phải là số nguyên từ 1 đến 5); `--mode day --days 6` → 2 (đầu vào sai: --days phải là số nguyên từ 1 đến 5); `--mode gather --days 2` → 2 (đầu vào sai: --days chỉ dùng với --mode day); file đầu ra KHÔNG tạo |
