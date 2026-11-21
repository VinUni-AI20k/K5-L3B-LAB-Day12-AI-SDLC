# Phân công theo phase · Quán Ăn Chợ Nổi

## Phase 1 · 60 phút

Bàn giao hai ca chơi được, HUD và smoke hai tiến trình theo Test Contract v1.0. Kế hoạch dùng starter Python. Điền tên thật và GitHub handle tương ứng TV1–TV5 vào TEAM.md trong kickoff. [Đề Phase 1](../PHASE-1.md)

| Người | Phần sở hữu và cách bắt đầu độc lập | Bằng chứng bàn giao |
|---|---|---|
| TV1 · Bơi và sinh tồn | Dùng scenario đặt sẵn giỏ, Máu và oxy. Kiểm tra bơi/chặn biên, viết lặn/nổi, oxy, ngạt, ngất và bỏ giỏ theo LIFO. Sở hữu GatherSim.step để ghép hàm của TV2. | Test oxy vừa hết ở t thì ngạt ở t+59. Nổi đúng bước đó thì hồi oxy. Khi ngất, lost đúng thứ tự, faint đứng trước gather_end và kho rỗng. |
| TV2 · Thu hoạch và kho | Dùng fixture đặt sẵn nhân vật, cây, cá và giỏ. Viết hàm hái/bắt riêng, xử lý ưu tiên bến, hòa theo ID, mọc lại, cooldown và sức chứa. Kiểm tra xuất kho bằng runner. | Giỏ thiếu chỗ giữ nguyên đàn cá và cooldown. Hái ở bước cuối vẫn vào kho. Cập bến ở bước cuối cho docked. Chạm tick_limit sớm giữ nguyên file kho. |
| TV3 · Khách và nguyên liệu | Dùng kho mẫu để viết lịch khách, chọn món theo seed, giữ nguyên liệu, kiên nhẫn và dọn đơn khi khách rời. Kiểm tra fixture khách và reserved theo mục D. Bàn giao các hàm xử lý khách cho TV4. | Test bàn bận bỏ lượt, thiếu món phát no_dish, khách mới giảm kiên nhẫn từ bước sau. Khi khách bỏ đi, nhả phần giữ và bỏ món của đơn, nguyên liệu đã nấu không hoàn lại. |
| TV4 · Bếp và thanh toán | Dựng sẵn khách reserved, bàn và kho để làm bếp → tay → bàn → thu tiền. Sở hữu QuanSim.step và thứ tự mục F. Kiểm tra liên kết đơn/bếp/tay, giá món, boa, uy tín và điểm. | Test phục vụ đúng tick kiên nhẫn về 0 vẫn hợp lệ. Phục vụ đúng lúc đóng cửa thì thu tiền một lần trước quan_end. Khách chờ rời do closing giữ nguyên uy tín. |
| TV5 · HUD, QA và release | Dùng snapshot fixture để làm HUD ngay. Ca sáng hiện giờ, oxy, Máu, giỏ. Ca tối hiện kho khả dụng, đơn, kiên nhẫn, bếp, tay, tiền và uy tín. Chạy smoke mục G trên starter và lập ma trận kiểm chứng. | Ảnh HUD cả hai ca, log kho thật từ hai tiến trình trên main và phép so từng byte khi chạy lại cùng seed/input. Tổng hợp bằng chứng của cả nhóm và đẩy tag. |

### Hợp đồng để làm song song

- TV1 và TV2 dùng chung hold theo thứ tự nhặt. TV1 điều phối vòng tick, TV2 viết các hàm thao tác thu hoạch và test riêng.
- TV3 giữ nguyên liệu trên từng đơn. TV4 trừ tồn vật lý và xóa phần giữ khi bắt đầu nấu. TV4 gọi xử lý tương tác trước khi TV3 xét khách hết kiên nhẫn. Hai người thống nhất điểm gọi hàm dọn đơn từ kickoff.
- TV3, TV4 và TV5 dùng ngay [kho mẫu](contracts/inventory.sample.json). TV2 xuất kho thật trước phút 25. TV5 chạy scenario cập bến mục G rồi xác nhận snapshot quán ở tick 0 có đúng 2 bông súng và 1 cá lóc.
- Mỗi người sở hữu test và bằng chứng của lát mình. UI gửi input và đọc snapshot từ cùng mô phỏng với headless.

### Mốc bàn giao

| Phút | Việc cần chốt |
|---|---|
| 0–15 | TV5 kiểm tra fork public, quyền collaborator, TEAM.md và team_size = 5. Cả nhóm chốt thỏa thuận, schema kho, sự kiện và giao diện sim/UI rồi chạy fixture từng lát. |
| 15–45 | Phút 20 rà lát vướng, trước phút 25 thử kho thật. TV1 và TV4 ghép từng cặp. TV5 đối chiếu HUD với snapshot. |
| 45–55 | Trên main, chạy suite bằng một lệnh, smoke hai tiến trình và chơi thử cả hai ca. Mỗi người lưu bằng chứng thật ở docs/proof/phase-1/. TV5 ghi yêu cầu, cách kiểm, bằng chứng và kết quả vào docs/verification/phase-1.md. Kiểm tra README có điều khiển, cách tính điểm, lệnh test và cách chạy từ clone sạch trong tối đa 3 lệnh. |
| 55–60 | TV5 đẩy tag phase-1 trỏ đúng commit bàn giao trước mốc 1:00. Cả nhóm hoàn tất clarify, AI usage log, retro và phản tư cá nhân theo mục 6.3. |

Trong cả buổi lab, mỗi người cần ít nhất 3 commit có nội dung bằng tài khoản đã khai. Nhóm 5 người cần hoàn thành ít nhất một mục mở rộng trong cả buổi. Bổ sung phase kế tiếp vào file này khi có đề.

## Phase 2 · Một ngày ở chợ nổi · 55 phút

Dùng [TICKET-02](../PHASE-2.md) và [hợp đồng v1.1](contracts/phase-2.md). Giữ số TV theo Phase 1. TV1 điều phối tích hợp, TV5 phụ trách release.

| Người | Phần sở hữu và cách bắt đầu ngay | Kiểm chứng bàn giao |
|---|---|---|
| TV1 · Trưởng nhóm | Giữ GatherSim.step, chuẩn hóa bơi/oxy/Máu, ghép Cá Sấu và nhận day/active_upgrades từ TV4. Dựng fixture quái trùng tâm, giỏ lẻ và HP=1. | Một hit mỗi bước, rơi LIFO, recoil đủ 60 bước, ngạt xuyên bất tử. D3 có M2. Ngất vẫn mở quán với kho rỗng. |
| TV2 · Thu hoạch | Làm bảng điểm sinh, 3 loài cá, chuyển động/phản xạ, đổi hướng, sinh theo seed, N5/N6 và 6 loại nguyên liệu ở bộ đọc kho. Viết logic cá độc lập rồi ghép với TV1. | Kiểm tra 8 vị trí ban đầu khác nhau, đúng tick 120/360, giới hạn 12 đàn, random_fish=false và bắt trước khi cá bơi. |
| TV3 · Quán và kế hoạch | Phụ trách dữ liệu 6 món, 2 bếp/4 bàn, kế hoạch D1–D5 và tổng nguyên liệu theo công thức. Dùng fixture kho mẫu để kiểm tra giữ chỗ, lọc món, bếp và thu tiền. | Quán độc lập dùng đủ menu. Trong day, đơn chỉ thuộc kế hoạch, suất dự kiến không giới hạn số bán. Hai đơn không tiêu trùng nguyên liệu. |
| TV4 · Vòng ngày | Phụ trách CLI, scenario chung, runner, pause và Shop. Dùng fixture ở bến và ca tối rút ngắn để triển khai chuyển pha ngay. Nhận kho từ TV1/2 và API kế hoạch từ TV3. | Smoke 1 ngày và 2 ngày. Mua đúng giá ở tick đóng Shop, cấp có hiệu lực ngày sau, pause đứng timer, ngày cuối chỉ hoàn tất khi đóng Shop. |
| TV5 · UI/QA | Dùng snapshot mẫu theo hợp đồng để làm menu, intro, HUD hai ca, pause, kết quả, Shop và Summary. Sở hữu smoke liên tiến trình, đối chiếu snapshot và đo hiệu năng. | Ảnh HUD 1280×720, đo FPS và thời gian headless, log smoke, regression P1, ma trận kiểm chứng và tag. |

**Phút 0–5** chốt owner và fixture. **5–20** mỗi người triển khai/test lát mình. **Phút 20** TV2, TV3 và TV5 đối chiếu kho thật giữa hai tiến trình, lưu integration.* vào docs/proof/phase-2/. **20–35** TV1 ghép gather, TV4 ghép vòng ngày. **35–45** chạy day một/nhiều ngày, regression P1 và ghi lý do cho test đổi theo v1.1. **45–55** cập nhật verification, clarify, AI log, retro và đẩy tag phase-2 trên main của fork trước 1:55.
