# Hợp đồng tích hợp Phase 2 · Test Contract v1.1

Áp dụng thay đổi của [TICKET-02, mục 4](../../PHASE-2.md) lên [hợp đồng Phase 1](phase-1.md). Các số liệu, ID, công thức và payload lấy nguyên văn theo mục 1–4 của ticket. Bản phân công chỉ định người triển khai tại [Phase 2](../phan-cong.md#phase-2--một-ngày-ở-chợ-nổi--55-phút).

## Quyền sở hữu dữ liệu

- TV1 giữ thứ tự GatherSim.step và tuning sinh tồn, monsters. TV2 giữ tuning cá/nút/giỏ, fish_initial chuyển thành số 8. TV3 giữ quan, menu và day_plan. TV4 giữ shop, CLI, contract_version và ghép các khối vào manifest chung. Mỗi người bàn giao phần kiểm tra fixture tương ứng cho TV4.
- day_plan gồm 5 mục {day,dishes,ingredients}. TV3 tính ingredients bằng tổng công thức nhân suất. TV4 nhận override theo ngày, tính lại và đối chiếu ingredients nếu có. TV5 đọc kế hoạch này để hiển thị đã lấy/cần.
- Hai nguyên liệu mới là ca_keo và keo_neo. Kho bàn giao dùng cùng object {"items":{...}} cho cả hai tiến trình độc lập và chuyển pha trong bộ nhớ. Đối chiếu gather_end.data.inventory.items với snapshot stock đầu quán. Tiền ca không nằm trong kho.

## TV1 ↔ TV2 · Một bước gather

Timer/cooldown/bất tử/hồi nút → bơi và oxy/ngạt → cập nhật quái theo ID và xét một hit → bến hoặc hái → bắt theo vị trí cá đầu bước → xét hết giờ → cá bơi rồi sinh. Ngất dừng bước ngay. Ngạt không làm rơi hàng khi còn Máu. monster_hit bỏ floor(n/2) theo LIFO, faint do quái bỏ phần còn lại. Chạm trùng tâm dùng +x, bất tử 90 tick, recoil 60 bước sau hit. M2 hoạt động từ D3, gather độc lập dùng D1.

TV2 dùng RNG có seed, age_ticks riêng cho cá, phản xạ phần quãng đường dư và đổi hướng trước bước bơi thứ 120·k. Sinh sau chuyển động ở phase_tick = 360·k, khoảng cách phải > 1 m, chuẩn hóa trọng số theo loài còn điểm. random_fish=false tắt cá mặc định, bơi và sinh. Event mới gồm fish_spawned(id,kind,pos), monster_hit(monster_id,hp,lost,pos) và faint(cause,lost,hp).

## TV3 ↔ TV4 · Day, quán và Shop

- CLI thêm --mode day và --days 1..5, mặc định 1. Hai cờ inventory chỉ dùng ở mode độc lập. Trong day, gather và quan là fixture khởi tạo mỗi ngày. Cấm quan.stock và quan.reputation. Kiểm liên kết đơn/giữ chỗ với kho thực khi mở quán, mâu thuẫn trả mã 2.
- Day sở hữu money, earned, reputation, upgrades và active_upgrades. Tiền đầu kỳ khai cả money lẫn earned, 0 ≤ money ≤ earned. Mở quán bằng kho thực, kể cả kho rỗng sau ngất. TV3 lọc ID món trong day_plan rồi lọc theo tồn khả dụng. Quán độc lập dùng cả 6 món.
- Tại tick 0 phát day_start → day_plan → phase_start(gather). gather_end → phase_start(quan), quan_end → phase_start(shop) cùng tick. Event kết thúc mang pha cũ, snapshot mang pha mới với phase_tick=0. Gameplay pha mới bắt đầu bước kế. Event trong day có trường day.
- Shop xử lý buy trước shop_done. Oxy cấp 1/2 giá 200/400, tối đa 2700/3600 tick. Máu cấp 1/2 giá 250/500, tối đa 4/5. Thành công chỉ trừ money và tăng upgrades. earned và điểm giữ nguyên. Lệnh lỗi phát buy_failed(action,reason). Cạnh shop_done thắng timeout ở tick 600, shop_end.reason là done hoặc time. Chỉ khi đóng Shop mới tăng days_completed. Đủ ngày trả days_complete, nếu chơi tiếp thì bỏ kho dư, sao cấp sang active_upgrades, khởi tạo đầy oxy/Máu và giỏ mới.
- Snapshot mọi pha trong day có day, day_plan, upgrades và active_upgrades. Shop có stock dư và time_left_ticks. bought mang upgrade,level,price,money. Điểm bằng earned + 100 × floor(reputation).

## TV4 ↔ TV5 · Input, pause và màn hình

Pause áp dụng cả ba mode, xét cạnh lên trước gameplay. Khi pause chỉ tăng tick ngoài, cập nhật chốt phím và phát paused khi vừa vào. Bỏ hành động và buy trong lúc pause. Cạnh tiếp theo phát resumed và chạy gameplay ngay bước đó. Giữ nút qua đổi pha không tạo cạnh mới. buy chỉ chạy ở frame khai báo.

UI thể hiện DayIntro → gather → EveningIntro → quan → DayResult → Shop → ngày mới/Summary. Headless chỉ có phase gather, quan, shop. UI lấy dữ liệu từ snapshot/event, dùng paid/served/customer_left để tổng hợp kết quả. DayIntro tự chuyển sau 4 s hoặc khi bấm phím. Kiểm tra cảnh báo oxy <25%, giờ ≤30 s, kiên nhẫn <25% và chữ ≥18 px ở 1280×720.

## Fixture tích hợp và điều kiện bàn giao

1. TV2/3 dùng fixture cập bến của Phase 1 và thêm ca mang ca_keo/keo_neo, đối chiếu file kho với stock ở tick 0 của quán.
2. TV4 dựng day.money=day.earned=200, cho cập bến ngay và rút ngắn ca tối. Tại Shop mua oxygen và đóng cùng frame. TV5 kiểm money=0, earned=200, oxy tối đa D2 bằng 2700 và days_completed đúng khi kết thúc.
3. TV5 đo một ngày đủ thời lượng, không pause, ≤22.200 tick và ≤20 s trên máy chấm, chơi thường trung bình ≥30 FPS ở 1280×720. Lưu điều kiện đo thực tế, bằng chứng và kết quả từng yêu cầu trên commit bàn giao.
4. Lõi dùng burn_s=null. Mở rộng có mã chỉ khai ở extensions khi nhóm thực hiện và có bằng chứng. Kỳ vọng một mục mở rộng cho nhóm 5 người tính trên cả buổi lab.
