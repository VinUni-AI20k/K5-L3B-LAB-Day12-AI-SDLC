---
name: verify-tag
description: Kiểm chứng repo Quán Ăn Chợ Nổi tại từng tag (phase-1…phase-4, v1.0.0) — xuất mã của tag ra thư mục tạm sạch, chạy unittest + smoke headless ở đó, kiểm tag đã đẩy lên remote, in bảng Markdown để dán vào docs/verification/phase-n.md. Dùng ngay sau khi gắn tag, trước khi viết/cập nhật ma trận truy vết, trước khi tạo Release, hoặc khi cần chứng minh "chạy được tại từng tag".
---

# verify-tag — kiểm chứng tại tag

Đề yêu cầu **chạy được tại từng tag**. Bằng chứng trong `docs/verification/` từng ghi "chưa commit — phải chạy lại
ở commit gắn tag" rồi không ai chạy lại. Skill này chạy lại thật trên **đúng mã của tag** (không lẫn file đang sửa
trong working tree) và in kết quả để dán vào bằng chứng.

## Khi nào dùng
- Ngay sau khi Integrator gắn tag `phase-n` (và sau khi đẩy tag).
- Trước khi viết hoặc sửa `docs/verification/phase-n.md`, trước khi tạo Release `v*`.
- Khi nghi một tag cũ bị vỡ do sửa file dùng chung (test, contract).

## Cách chạy (từ gốc repo)
```bash
python3 .agents/skills/verify-tag/verify_tag.py                   # mọi tag phase-* và v*
python3 .agents/skills/verify-tag/verify_tag.py phase-3 phase-4   # chỉ các tag này
python3 .agents/skills/verify-tag/verify_tag.py --offline         # không hỏi remote
```
Windows: thay `python3` bằng `python`. Mỗi tag mất khoảng 10–60 s.

## Lệnh này làm gì với mỗi tag
1. `git archive <tag>` → giải nén vào thư mục tạm (working tree không bị đụng, không tạo worktree).
2. Chạy `python3 -m unittest discover -s tests` trong thư mục đó, đọc số test và OK/HỎNG.
3. Smoke headless: `gather` 600 tick; nếu `contract_version` của tag ≥ 1.1 thì thêm `day` 1 Ngày (≤ 20 s).
4. So với `git ls-remote --tags origin` xem tag đã đẩy chưa, và remote có trỏ đúng commit không.
5. In bảng Markdown, xóa thư mục tạm. Thoát mã 1 nếu có tag hỏng hoặc lệch remote.

## Sau khi chạy — cập nhật bằng chứng
1. Dán bảng vào `docs/verification/phase-n.md`, mục "Kiểm chứng tại tag", thay các ghi chú kiểu
   "chưa commit / phải chạy lại ở commit gắn tag".
2. Ghi đúng sự thật: tag hỏng thì ghi hỏng và nguyên nhân. **Không** di chuyển hay gắn lại tag đã đẩy khi chưa hỏi
   Integrator; sửa ở commit mới và ghi vào phase sau.
3. Nếu cần tái tạo bằng chứng của phase: `bash docs/proof/phase-n/run_proof.sh`. Script này **ghi đè** file trong
   `docs/proof/phase-n/`, nên chỉ chạy khi định commit lại bằng chứng.
4. Agent làm việc này thì thêm một dòng vào `docs/ai-usage-log.md` (việc, kết quả, AI sai ở đâu nếu có).
