# Chạy thật Phase 2 (s0ra1n0, trước khi gắn tag phase-2)

## day --days 1
- mã thoát 0, thời gian 0.84 s, 2 lần cùng seed: GIỐNG từng byte
- end: reason=days_complete, ticks=22200, days_completed=1
- day_plan công bố: [{"ca_loc_nuong_trui": 3, "goi_bong_sung": 3}]

## day --days 5
- mã thoát 0, thời gian 3.81 s, 2 lần cùng seed: GIỐNG từng byte
- end: reason=days_complete, ticks=111000, days_completed=5
- day_plan công bố: [{"ca_loc_nuong_trui": 3, "goi_bong_sung": 3}, {"ca_loc_nuong_trui": 2, "lau_ca_linh_dien_dien": 2}, {"goi_bong_sung": 2, "canh_chua_ca_loc": 2, "ca_keo_nuong": 2}, {"lau_mam": 1, "ca_loc_nuong_trui": 2, "goi_bong_sung": 1}, {"lau_mam": 1, "lau_ca_linh_dien_dien": 1, "ca_loc_nuong_trui": 1}]

## Smoke tích hợp gather --inventory-out → quan --inventory (v1.1, có kind mới)
- kho ghi: {"items": {"bong_sung": 2, "ca_keo": 1, "ca_loc": 1, "keo_neo": 1}}
- stock quán tick 0: {"bong_sung": 2, "ca_keo": 1, "ca_loc": 1, "keo_neo": 1} → KHỚP

## Mở rộng burn (manifest `extensions: ["burn"]`, `burn_s: 20`)
- Quán: khách C1 gọi cá lóc nướng trui, kho 2 cá lóc, nấu ở tick 0, để món trên bếp.
- Sự kiện: [(361, 'dish_ready', None), (1562, 'dish_burnt', 'reserved')] → cháy khi ready_ticks = 1201 > 1200, đơn giữ lại thành reserved (kho còn cá lóc).

## Tốc độ cá (AC-P2-02), gather seed 1, 1500 tick
- 112 đoạn 1 s bơi thẳng: quãng min 1.475 m, max 1.501 m (chuẩn 1.5 m/s; 1.475 = cá mới sinh chỉ bơi 59 bước). Lỗi chéo 2.086 m/s cũ không còn.
