# Kiểm chứng Phase 2 · phần TV1

Các kết quả dưới đây được chạy trên workspace nhánh `sang/tv1` sau commit Phase 1 `0d867a1`. Khi tích hợp lên main, QA chạy lại trên SHA bàn giao.

| Mục TICKET-02 | Cách kiểm | Kết quả trên nhánh |
|---|---|---|
| §1.2, §4.5 · Cá Sấu và ngất | Kiểm hòa khoảng cách theo ID, recoil đủ 60 bước, bất tử 90 tick, ngạt xuyên bất tử, rơi hàng LIFO, ngất mở quán cùng tick. | Đạt trong [test TV1](../../tests/test_phase2_tv1.py). |
| §2, §4.2 · Pause, Shop và nâng cấp | Pause ở gather/quan/Shop, giữ nút qua bước resume, mua đúng giá, kiểm cấp mua/cấp đang áp dụng, đóng Shop ở bước cuối. | Đạt trong test TV1. |
| §4.1–4.5 · Day và scenario | Kiểm ngày vượt miền, kế hoạch ghi đè, số tiền đầu kỳ, fixture quán đối chiếu kho khi chuyển pha, M2 xuất hiện từ D3. | Đạt trong test TV1. |
| §5 · Smoke độc lập và nhiều ngày | Kiểm kho hai tiến trình. Chạy day seed 42 hai lần, so SHA-256. Chạy đủ 5 ngày và đọc dòng end. | Kho khớp. 1 ngày 22.200 tick, hai lần có cùng SHA-256. 5 ngày 111.000 tick. [Lệnh và kết quả thực tế](../proof/phase-2/integration.tv1.txt) |

Hồi quy trên nhánh đạt 62/62 test, gồm 9 test TV1 mới. V1.1 nhận mode `day` và nhận nút boolean `attack` dù mở rộng tắt. Vì vậy các test v1.0 từng yêu cầu từ chối hai đầu vào này đã đổi theo §4.1–4.2. Input lạ hoặc sai kiểu vẫn phải thoát mã 2.

TV2 còn tích hợp preset 8 đàn, chuyển động và sinh cá. TV3 còn tích hợp lịch sinh khách trên nền hai bếp/bốn bàn và thực đơn theo ngày. TV5 còn nối HUD/menu, điều khiển trực tiếp và đo FPS. QA cần đo lại trên bản đủ các lát. Thời gian trong log là kết quả máy phát triển.
