# Kiểm chứng Phase 4

Kết quả trên bản làm việc dựa trên `4d5ab31`. Bài kiểm UI dùng Edge headless ở 1280×720 và cấp snapshot mẫu qua `/state`.

| Hạng mục | Kết quả |
|---|---|
| Ba cảnh báo và tương phản cao | Đạt với fixture. Sau khi bấm nút tương phản cao, Canvas vẽ đủ cảnh báo oxy thấp, thủy quái gần và khách bàn T1 sắp giận. Tùy chọn được ghi vào bộ nhớ trình duyệt. |
| Phụ đề khi tắt tiếng | Đạt với fixture. Sau khi bấm nút tắt tiếng, event `oxygen_empty` hiện phụ đề. Không có bộ phát âm nào được tạo. |
| Tính tất định của Gather | Hai lần chạy seed 42, 600 tick cho cùng SHA-256 `5011e798003dedf262ee4f219a82061912725b9da18ccdf64e735c6748b9c714`. |
| Regression | 93 bài, 88 đạt, 4 thất bại, 1 lỗi. Ba bài Day/Pause/Shop gặp CLI chưa nhận `--days`. Hai bài còn lại liên quan trọng số sinh cá và thời gian bất tử/recoil. |
| Một ngày hoàn chỉnh, benchmark, soak, tag và release | Chưa có bằng chứng bàn giao. Manifest đang ở v1.1. |

Chạy regression bằng `python -m unittest discover -s tests -v`. Kiểm tính tất định bằng hai lần chạy `python -m chonoi.headless --mode gather --seed 42 --ticks 600 --out <file.jsonl>`.
