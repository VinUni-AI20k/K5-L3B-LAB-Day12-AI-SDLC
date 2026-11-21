# Ma trận truy vết Phase 4

Bản QA kiểm thử: `main` tại `0538d68`, Windows PowerShell.
Kết quả dưới đây thuộc bản baseline. Cập nhật SHA và chạy lại trên commit bàn giao.

| AC | Yêu cầu | Bằng chứng / cách kiểm | Kết quả baseline |
|---|---|---|---|
| AC-P4-01 | Manifest v1.3 khai lệnh benchmark và soak | Đọc `game.contract.json` | Chưa đạt: `contract_version` là `1.1`, thiếu `bench_cmd` và `soak_cmd`. |
| AC-P4-02 | Benchmark render seed 42, 1280×720, làm nóng 3 s, đo 30 s | [Kết quả đo QA](../proof/phase-4/bench-qa-d5e14bf.json) trên `d5e14bf` | Runner v1.1 xuất đủ 5 trường. FPS trung bình 144,03 và tải 941 ms đạt mốc. Giá trị 1% low 133,16 dùng nghịch đảo p99 thời gian khung. Chờ sửa công thức Ticket 04 và đo lại. |
| AC-P4-03 | Soak 10 Ngày, không crash, kết quả gameplay lặp lại | Chạy seed 7 hai lần, so kết quả trừ `duration_s` | Chưa chạy: thiếu `soak_cmd`. |
| AC-P4-04 | Regression P1–P3 còn hiệu lực | Lệnh chạy và lỗi bên dưới | 57/64 đạt tại `0538d68`. |
| AC-P4-05 | Ba cảnh báo dễ nhận biết khi bật tương phản cao | Kiểm thủ công bản xem `?preview=2` trên `d5e14bf`, bật Tương phản cao | Đạt 3/3 trên snapshot mẫu: “Oxy thấp!”, “Thủy quái!” và “Khách sắp bỏ đi · 6 giây” tại bàn T3. Chờ kiểm live trên commit bàn giao. |
| AC-P4-06 | Clone sạch chạy UI trong tối đa 3 lệnh trên macOS/Linux | Ghi môi trường, lệnh README và kết quả mở UI | Chưa kiểm trên bản bàn giao. |
| AC-P4-07 | Tag `phase-4` và Release `v1.0.0` cùng SHA trên `main`, có gói chạy được | Đối chiếu SHA, release notes và tệp đính kèm | Chờ bản bàn giao. |

## Regression baseline

```powershell
$env:PYTHONPATH = 'tests;.'
python3 -m unittest discover -s tests -v
```

64 test, 7 lỗi, 12,745 giây.

- P2: fixture Cá Sấu không gây ngất bị từ chối ở `hold`; CLI từ chối `--days 2`; parser từ chối `pause`.
- P3: gather từ chối `hold` dạng cá thể trong hai ca; quán vẫn chấp nhận kho đếm; quán từ chối `stock` dạng mảng cá thể.