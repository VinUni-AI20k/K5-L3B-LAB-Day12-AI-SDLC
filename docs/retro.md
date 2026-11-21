# Retro nhóm MMMMV

## Phase 2

Điều tốt: chia theo file chạy đúng. Bốn người, bốn vùng, gần như không conflict trong code. Cá Sấu, cá bơi, quán 2 bếp 4 bàn, `day` + Shop vào được; test từ 32 lên 185.

Điều tệ: mọi thứ đi qua `main` bằng push trực tiếp, bốn lần. PR có nhưng PR #2 do chính tác giả merge. Và cái HUD vòng ngày (`day_plan`, màn Shop, pause) không ai làm, nên `phase-2` đến giờ vẫn chưa tag được dù backend xong.

Hành động cho Phase 3: gộp 4 skill còn 2, và thêm một cổng kiểm bằng chứng — claim "đạt" phải có file thật.

## Phase 4

Rà hành động Phase 2: cổng bằng chứng đã có (`tools/check_evidence.py`, chạy trong `run_checks`). Việc gộp skill thì chưa làm.

Điều tốt: test là thứ giữ nhóm lại. 185 test, tất định từng byte, và cổng `run_checks.py` bắt được lỗi thật — một `quan_end` phát hai lần, một test lệch tick. Bench chạy trên Playwright: 60 FPS, 1% low 59,5.

Điều tệ: bằng chứng bị viết trước khi có. PR #15 đánh dấu sáu AC "đạt" với năm file proof không tồn tại, và viết hộ phản tư của ba người. Phát hiện bằng cách mở đúng đường dẫn và đếm test thật.

Số liệu: 50 commit không tính merge — Văn Minh 24, Vinh 14, Cao Minh 11, Đức Minh 8, Nhật Minh 6. Cách đọc code: review chéo theo vòng, nhưng có lần không ai đọc trước khi merge.

Một lần AI sai: lần rõ nhất là AI sinh ma trận AC-P4 với đường dẫn proof nghe rất hợp lý nhưng không tồn tại; `ls docs/proof/phase-4/` chỉ có một file. Lần nhỏ hơn: test `dish_ready` của tôi khẳng định tick 360, chạy ra 361 vì event ghi ở `k+1`.

Nếu làm lại: dựng `run_checks.py` và ma trận ngay phút đầu, và cấm push thẳng `main` từ commit đầu tiên.
