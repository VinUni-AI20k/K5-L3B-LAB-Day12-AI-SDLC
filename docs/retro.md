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
