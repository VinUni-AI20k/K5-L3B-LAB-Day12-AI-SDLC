# Đội Phoenix

**Số thành viên:** 3

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Lê Nguyễn Anh Khôi | KN-16 | HUD, runner, hợp đồng và tích hợp | Nhóm trưởng, PO, QA lead, Release | Diên và Nhân ở giao diện tích hợp |
| Đinh Phúc Diên | dinhphucdien179 | Lặn & Hái | Phụ trách gather và kiểm thử lát | Nhân khi chạy smoke đầu-cuối |
| Lê Nguyễn Anh Nhân | ying684 | Mở Quán | Phụ trách quan và kiểm thử lát | Diên khi chạy smoke đầu-cuối |

## Thỏa thuận làm việc

- Dùng kênh chat hiện có của nhóm. Chốt đầu phase và standup ở phút 20. Báo vướng quá 10 phút.
- Khi bất đồng, trao đổi trong 2 phút, sau đó Khôi chốt và ghi lý do.
- Codex hỗ trợ đối chiếu yêu cầu, gợi ý và soạn nháp. Thành viên phụ trách review phần của mình. Khôi review, quyết định và xác nhận tài liệu hoặc thay đổi dùng chung trước khi nhóm đưa vào repo.
- Khôi đẩy kickoff lên `main`. Mỗi người phát triển trên nhánh riêng, test, commit bằng tài khoản của mình và mở PR. Gộp bằng merge commit để giữ lịch sử tác giả.
- Mỗi người có ít nhất 3 commit có nội dung. Khi làm chung một commit, ghi `Co-authored-by:` cho người cùng làm.
- Chờ SHA của phần phụ thuộc trên `main`, sau đó cập nhật bằng `git pull --ff-only origin main` rồi tiếp tục. Khôi kiểm bản tích hợp và đẩy tag từng phase.
