# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt: chia lát theo hợp đồng v1.1 nên TV1–TV4 làm song song bằng fixture; TV5 làm UI từ snapshot mẫu trước khi có `--mode day`, lúc ghép chỉ đổi lớp lõi, client không phải sửa. Có một lệnh QA (`python3 tools/qa_p2.py`) chạy lại toàn bộ checkpoint trên commit bất kỳ.
- Điều tệ: `--mode day` vào main muộn (PR #11) nên smoke day và kiểm UI trên DaySim thật dồn về cuối phase; `chonoi/live.py` bị hai người sửa cùng lúc (TV4 + TV5) gây xung đột khi gộp.
- 1 hành động cho Phase 3: mỗi file dùng chung (`live.py`, `runner.py`, `game.contract.json`) có một chủ duy nhất ghi trong `docs/phan-cong.md`; người khác sửa qua PR nhỏ có tag chủ file review. **Người nhận: TV5 (Vũ Xuân Bách)** cập nhật bảng chủ file đầu Phase 3 và nhắc trong standup phút 20.

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:

## Ghi nhận Phase 2 · TV1

- Điều tốt là fixture headless kiểm được ranh giới hit, recoil và LIFO trước khi có vòng ngày/UI.
- Vướng mắc hiện tại là CLI và manifest đang v1.0 nên các ca chuyển ngày cần TV4 tích hợp.
- TV1 và TV4 nhận hành động kiểm day=3 sinh M2 và ngất mở quán kho rỗng khi vòng ngày có mặt.

## Ghi nhận Phase 3 · TV4

- Ghép tạm các diff TV2 và TV3 giúp kiểm được handoff, ID xuyên ngày và dòng thanh toán trước khi đổi manifest.
- Ca nấu sau đúng 60 bước cho thấy sai số của kho thô đi vào phép chốt giá. Giữ ca này trong kiểm chứng khi TV1/TV3 ghép cách biểu diễn độ tươi dùng chung.

## Ghi nhận Phase 3 · TV5

- **Rà hành động Phase 2 (bảng chủ file):** phân công Phase 3 đã ghi chủ từng file (TV1 `inventory.py`/`contract_version`, TV3 `QuanSim.step`, TV5 client/QA). Kết quả: lần gộp main vào nhánh TV5 không có xung đột code; TV1 chỉ sửa 4 dòng `chonoi/live.py` trong PR của mình. Đã làm, giữ cho Phase 4.
- **Điều tốt:** checkpoint chạy bằng CLI trên bản sao bật 1.2 nên kiểm được v1.2 khi manifest chưa bật mà không đụng file của TV1; HUD làm từ snapshot mẫu trước, ghép sim thật chỉ phải nới bố cục.
- **Điều tệ (rút ra từ lần đổi kho):** đổi schema kho làm vỡ fixture ở 9 file test của 4 người; các lát tự đạt test của mình trên 1.1 nên tới cuối phase mới thấy 18 test hỏng khi bật 1.2.
- **1 hành động cho Phase 4:** khi đổi hợp đồng dữ liệu, TV5 chạy `qa_p3.py` (CP8b — suite trên bản bật version mới) ngay phút 20 và gửi danh sách test hỏng theo chủ lát vào standup. **Người nhận: TV5 (Vũ Xuân Bách).**
