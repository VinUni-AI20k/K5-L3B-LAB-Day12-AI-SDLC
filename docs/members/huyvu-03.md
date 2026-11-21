# huyvu-03 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - `M1.1` ([`d15883d`](https://github.com/huyvu-03/K5-L3B-LAB-Day12-AI-SDLC-NhomABC/commit/d15883dd33e601ced58cdac1e7933c43113a8c08)): Viết tiêu chí chấp nhận cho bơi, chặn biên, oxy, ngạt, Máu và ngất.
  - `M1.2` ([`d15883d`](https://github.com/huyvu-03/K5-L3B-LAB-Day12-AI-SDLC-NhomABC/commit/d15883dd33e601ced58cdac1e7933c43113a8c08)): Thêm bốn test headless từ tiêu chí chấp nhận.
  - `M1.3` ([`d15883d`](https://github.com/huyvu-03/K5-L3B-LAB-Day12-AI-SDLC-NhomABC/commit/d15883dd33e601ced58cdac1e7933c43113a8c08)): Triển khai `dive`, `surface`, oxy, ngạt và ngất.
  - `M1.4` ([`d15883d`](https://github.com/huyvu-03/K5-L3B-LAB-Day12-AI-SDLC-NhomABC/commit/d15883dd33e601ced58cdac1e7933c43113a8c08)): Chạy test và ghi [bằng chứng kiểm thử](../proof/phase-1/m1.md).
- **Tôi đã review (kèm link):** Đối chiếu các assertion của [bộ test M1](../../tests/test_gather_m1.py) với [thứ tự xử lý tick trong PRD-0](../../PRD0.md#L241). Review chéo với M2 chưa có link xác nhận.
- **AI sai ở đâu và tôi phát hiện thế nào:** AI dùng lệnh `python3` của repo, nhưng alias trên Windows không khởi chạy được. Tôi phát hiện khi kiểm tra phiên bản và dùng Python đã cài để chạy các tiến trình headless.
- **Điều tôi học được:** Viết test theo từng tick giúp bắt lỗi lệch một tick. Tick vừa cạn oxy đã tính vào thời gian ngạt, còn nổi đúng tick ngạt thì giữ nguyên Máu.
