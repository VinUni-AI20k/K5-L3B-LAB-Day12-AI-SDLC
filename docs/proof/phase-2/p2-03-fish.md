# Kiểm chứng P2-03, AC-P2-02

- `PYTHONPATH=tests:. python3 -m unittest discover -s tests` — **190/190 đạt**. Bảy test P2-03 kiểm tra đàn đầu ca, đổi hướng theo tuổi, phản xạ ở mép và góc, sinh theo lịch và sức chứa, khoảng cách nghiêm ngặt, thứ tự bắt trước khi bơi và fixture CLI.
- `python3 tools/check_determinism.py --seed 17 --ticks 4500` — JSONL `gather` và `quan` giống từng byte qua hai lần chạy, qua nhiều mốc sinh cá.
- `python3 tools/check_no_hardcode.py` — không có literal tuning đáng ngờ.
- `python3 tools/smoke_phase1.py` — **27/27 mục đạt**, gồm bàn giao kho `gather` → `quan`.

Đàn đầu ca dùng quy tắc sinh định kỳ theo giả định đã ghi ở `docs/clarify.md` câu 8. Điểm sinh so với vị trí hình học của mọi đàn, kể cả loài khác. `random_fish: false` giữ nguyên vị trí, hướng và tuổi fixture. Fixture Phase 1 cần hành vi đứng yên được đặt cờ rõ ràng. Smoke snapshot kiểm đúng số đàn khai trong contract, thay cho điều kiện tạm khi P2-03 chưa có.

`chonoi/scenario.py` được bổ sung kiểm `fish[].age_ticks` và miền bơi cho fixture có bơi. Loader nhận tuổi ở v1.1, cá fixture đứng yên vẫn dùng miền nước như Phase 1. Mã tuân theo Test Contract v1.1 mục 1.1, 4.3 và 4.5.
