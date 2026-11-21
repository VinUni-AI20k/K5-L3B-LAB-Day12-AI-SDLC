# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt: Chia 2 người phụ trách trọn lõi Phase 2 (TV1 `gather`/`monsters`/`contract v1.1`, TV3 `quan`/`day`/`shop`/`pause`/`burn`) giúp merge không xung đột file code; mở rộng `burn` đã có sẵn test từ cuối P1 nên bật chạy xanh ngay.
- Điều tệ: `chonoi/scenario.py` khối `day` và cập nhật `test_smoke_p1.py` bị dồn sang bước tích hợp cuối; phần UI Menu/Pause/HUD vòng ngày của TV4 chưa kịp gộp trước tag `phase-2`.
- 1 hành động cho Phase 3: Ngay 5 phút đầu Phase 3, TV2 + TV1 chốt trước adapter `chonoi/inventory.py` v1.2 và `scenario.py` trên nhánh tích hợp rồi mới ghép `gather`/`quan`/`day` (TV1 chịu trách nhiệm chốt & merge sớm).

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
