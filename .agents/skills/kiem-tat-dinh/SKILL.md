---
name: kiem-tat-dinh
description: Kiểm tất định theo Test Contract v1.0 (AC-P1-51) — chạy headless hai lần với cùng seed, tham số, đầu vào và so JSONL + file kho từng byte, cho cả gather và quan, nhiều seed. Dùng sau mọi thay đổi luật có dùng RNG, thứ tự duyệt thực thể, làm tròn số, hoặc trước khi gắn tag.
---

# Kiểm tất định (cùng seed → giống từng byte)

## Khi nào dùng
- Sau khi sửa luật dùng RNG (chọn món theo seed ở lát 3, cá bơi/sinh ở phase sau).
- Sau khi đổi thứ tự duyệt thực thể, cách sắp id, định dạng số hoặc ghi JSONL.
- Khi thêm phần "Sáng tạo của nhóm": bảo đảm nó tắt ở headless.
- Trước khi Integrator gắn tag `phase-n`.

## Cách chạy
Từ gốc repo:

```bash
python3 .agents/skills/kiem-tat-dinh/kiem_tat_dinh.py                      # seed 1, 42, -7; 3600 tick
python3 .agents/skills/kiem-tat-dinh/kiem_tat_dinh.py --seeds 1 2 3 --ticks 10800
python3 .agents/skills/kiem-tat-dinh/kiem_tat_dinh.py --proof docs/proof/phase-1
```

Mỗi seed chạy 4 kịch bản, mỗi kịch bản 2 lần, rồi so byte:
1. `gather` không điều khiển.
2. `gather` có inputs: lặn xuống, bắt cá, nổi lên, hái nút; ghi kho.
3. `quan` với kho mẫu `docs/contracts/inventory.sample.json`.
4. `quan` không kho.

Script còn kiểm một seed khác cho JSONL quán khác. Kiểm này chỉ cảnh báo, vì khi chưa có khách hai seed có thể ra giống nhau.

Mã thoát: 0 nếu mọi cặp giống từng byte, 1 nếu có cặp khác.

## Agent làm gì với kết quả
- Có cặp khác: script in dòng đầu tiên khác nhau. Tìm nguồn bất định:
  - `random` toàn cục, `time`, `datetime`;
  - duyệt `dict`/`set` không sắp xếp;
  - float chưa làm tròn trước khi so.
- Sửa theo quy tắc trong `AGENTS.md`: RNG chỉ qua `Streams`, sắp bằng `ids.sort_by_id`.
- **Không** nới phép so sánh cho xanh.
- Khi gắn tag: ghi kết quả vào `docs/verification/phase-n.md`, bằng chứng ở `docs/proof/phase-n/tat-dinh.txt`.
