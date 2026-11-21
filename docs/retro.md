# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt:
- Điều tệ:
- 1 hành động cho Phase 3:

## Phase 3 (nhanh) — đổi kho đếm sang kho cá thể
- Điều tốt: chốt giao diện chung trước (cá thể `fresh_u`, 240 đơn vị/điểm, `chonoi/fresh.py`) nên 5 lát làm song song gộp không conflict văn bản; test hộp đen `tests/test_fresh_p3.py` (24 AC) viết từ PRD trước khi có code, sau ghép đạt 24/24.
- Điều tệ: hai PR cùng sửa `chonoi/jsonl.py` để xuất fresh 6 chữ số, bản gộp gọi biến `key` không tồn tại → mọi headless crash, 121 test đỏ trên p3/integ. Merge phase 2 (`7932de0`) ghi đè 3 dòng ai-usage-log và phản tư của Toan bằng bản cũ trên `dev` — phát hiện khi làm phase 3, đã khôi phục.
- 1 hành động cho Phase 4: file dùng chung (jsonl.py, game.contract.json, inventory.py, docs/*) chỉ một người sửa mỗi lần; trước khi merge `dev` → `main` chạy `git diff main dev -- docs/` để không đè ghi chép.
- Ý kiến cá nhân: TODO(nhóm).

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
