# vm140205-collab — phản tư cá nhân

Làm quán trước, rồi mới tới phần khó hơn.

Ticket 04 của tôi là chuyện khách vào quán: đến theo lịch, giữ nguyên liệu, chờ, bỏ đi (`413fdfd`). Sau đó là prefactor v1.1 (`c84eac9`), Cá Sấu ở Phase 2 (`798680a`), rồi nối hook net vào `day` (`83e71a5`). Mấy tool tôi viết vì ghét làm tay: `run_checks.py`, `team_progress.py`, `bench.py`.

Lần tôi thấy rõ nhất việc AI bịa là khi review PR #15. Ma trận ghi "Đạt" cho sáu AC và dẫn năm file proof; cả năm đều không tồn tại. Chỉ cần mở đường dẫn là biết.

AI sai chỗ nào? Một test của tôi khẳng định `dish_ready` ở tick 360, chạy trên code thật ra 361, vì event ghi ở `k+1` mà tôi quên. Sửa thành `cook_started.tick + 360`.

Còn chưa chắc: bench 60 FPS là đo trên Chromium của Playwright; obscura trên máy tôi chỉ được 6 FPS. Không biết máy chấm sẽ ra số nào, nên tôi vẫn ghi rõ môi trường đo thay vì khoe con số.
