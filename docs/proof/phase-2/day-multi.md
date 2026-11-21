# Smoke nhiều Ngày + nâng cấp — phase-2

- Commit: `fe3930f` · Thời điểm: 2026-11-21 12:23

## A. `day --days 5 --seed 11` (không điều khiển)

- Mã thoát 0; 111000 tick; 1.9 s (≈ 0.38 s/Ngày, giới hạn 20 s)
- end: reason `days_complete`, days_completed 5
- Kế hoạch công bố:
  - D1: {'ca_loc_nuong_trui': 3, 'goi_bong_sung': 3}
  - D2: {'ca_loc_nuong_trui': 2, 'lau_ca_linh_dien_dien': 2}
  - D3: {'goi_bong_sung': 2, 'canh_chua_ca_loc': 2, 'ca_keo_nuong': 2}
  - D4: {'lau_mam': 1, 'ca_loc_nuong_trui': 2, 'goi_bong_sung': 1}
  - D5: {'lau_mam': 1, 'lau_ca_linh_dien_dien': 1, 'ca_loc_nuong_trui': 1}

## B. `day --days 3` có mua nâng cấp (money 700) — `day3.scenario.json`, `day3.inputs.json`

- Mã thoát 0; chạy lại cùng seed giống từng byte: True
- Shop:
  - tick 10802 (Ngày 1) `bought` {'upgrade': 'oxygen', 'level': 1, 'price': 200, 'money': 500}
  - tick 10803 (Ngày 1) `bought` {'upgrade': 'hp', 'level': 1, 'price': 250, 'money': 250}
  - tick 10804 (Ngày 1) `buy_failed` {'action': 'oxygen', 'reason': 'funds'}
  - tick 10805 (Ngày 1) `shop_end` {'reason': 'done'}
  - tick 33005 (Ngày 2) `shop_end` {'reason': 'time'}
  - tick 55205 (Ngày 3) `shop_end` {'reason': 'time'}
- Snapshot đầu buổi sáng mỗi Ngày (active_upgrades → oxy tối đa, Máu tối đa, quái):
  - Ngày 1: {} → oxygen_max_ticks 1800, hp_max 3, monsters ['M1']
  - Ngày 2: {'hp': 1, 'oxygen': 1} → oxygen_max_ticks 2700, hp_max 4, monsters ['M1']
  - Ngày 3: {'hp': 1, 'oxygen': 1} → oxygen_max_ticks 2700, hp_max 4, monsters ['M1', 'M2']

**Kết quả: ĐẠT** — kế hoạch D1–D5, chốt Ngày khi Shop đóng, cấp oxygen/hp áp từ Ngày kế, M2 từ Ngày 3, tất định.
