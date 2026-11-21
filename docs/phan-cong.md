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

## Phase 3 · Mùa Nước Nổi · 35 phút

Theo [TICKET-03](../PHASE-3.md), lõi Phase 3 chuyển kho đếm sang kho cá thể và tính độ tươi xuyên gather → quan → day. Giữ số TV theo phân công trước, người dùng nhận TV1. Tên/handle trong TEAM.md đang có chỗ lệch số TV, trưởng nhóm xác nhận lại khi kickoff.

### Phân việc chạy song song

| Người | Phần sở hữu / file cần đổi | Cách bắt đầu độc lập | Đầu ra và ca nghiệm thu |
|---|---|---|---|
| **TV1 · Bạn, trưởng nhóm** | Schema/adapter kho, độ chính xác của độ tươi, cấp/reserve ID và thứ tự tích hợp. Sở hữu inventory.py, ids.py nếu cần, hợp đồng dữ liệu, cấu hình freshness và contract_version trong game.contract.json. | Tạo fixture cá thể và helper kiểm schema, hao tươi, cấp ID, định dạng xuất. Bàn giao giao diện cho TV2–TV4 trong 7 phút đầu. | Đọc/ghi nguyên tử, id duy nhất và tăng xuyên ngày, kho đếm bị từ chối ở v1.2. Giữ đủ chính xác ngưỡng 30 và floor. Có test migration/schema. Ghi quyết định đổi kho và CHANGELOG. |
| **TV2 · Gather và mất hàng** | GatherSim, phần validate gather trong scenario.py và test ca sáng. TV2 giữ GatherSim.step cho phase này để ghép hao tươi, thu hoạch và LIFO. | Dùng hold fixture cá thể theo schema chốt, gọi adapter của TV1. | Hàng đầu bước giảm 0.5/s, hàng mới fresh=100 từ bước sau. spoiled một lần theo ID. Hái/bắt cấp I mới. monster_hit/faint lost là cá thể LIFO. Cập bến bàn giao sau hao, ngất kho rỗng. |
| **TV3 · Kho quán, giữ chỗ và ươn** | Kho cá thể trong QuanSim, available_stock, chọn món/giữ chỗ, _load_customer/_check_dishes và validate quan trong scenario.py. Sở hữu QuanSim.step để ghép với TV4. | Dựng kho có hai cá thể cùng loại khác độ tươi, đơn reserved và cá thể sát ngưỡng. | Giữ cá thể tươi nhất rồi ID. Kho giảm 0.25/s kể cả phần giữ. Phát toàn bộ spoiled theo ID rồi xử lý đơn bị ảnh hưởng theo order_tick/id bàn, nhả toàn bộ và thử giữ lại một lần. Thiếu hàng → unfulfillable. Kiểm reserved đủ công thức, chưa ươn, không trùng đơn. |
| **TV4 · Bếp, giá và vòng ngày** | _start_cooking trong QuanSim, payload món/thu tiền, DaySim và snapshot Shop. Phối hợp TV3 tại QuanSim.step, phần scenario day thuộc TV4. | Dựng đơn đã giữ các ID cụ thể để thử tiêu hàng/chốt giá mà không chờ lịch khách. | Tiêu đúng ID, cook_started.items theo kind rồi ID. Giá floor(niêm yết × fresh trung bình /100), boa theo giá đã chốt. Day giữ nguyên ID ngày đầu, ngày sau cấp mới theo thứ tự mẫu, bộ cấp ID không reset khi đồ bị dùng/bỏ. Chuyển pha không hao thêm, Shop không hao. Pause vẫn dừng hao. |
| **TV5 · HUD, QA và release** | Client/web, bộ smoke tích hợp, proof và verification Phase 3. Điều phối sửa fixture của các bộ test cùng chủ lát. | Dùng snapshot mẫu mảng cá thể để làm HUD và kịch bản kiểm ngưỡng/file/day ngay. | HUD đọc được độ tươi/hàng ươn. Smoke file so đúng ID/kind/fresh với snapshot quán tick 0. Smoke day, giữ lại nguyên liệu, chốt giá và regression P1–P2 còn hiệu lực. Lưu log/ảnh, chốt tag với trưởng nhóm. |

### Quyết định giao diện chốt lúc kickoff

- File kho có đúng một khóa items là mảng {id,kind,fresh}. hold và stock cũng là mảng cá thể. reserved là mảng ID. Kho rỗng dùng {"items":[]}. UI tự đếm theo kind từ cùng snapshot.
- TV1 cung cấp thao tác đọc/ghi/validate, cấp ID và hao tươi dùng chung. Hàm hao tươi trả danh sách cá thể vừa qua ngưỡng, caller gắn location và phát spoiled theo ID. Caller giữ thứ tự hold để phục vụ LIFO. Tên hàm và chữ ký cụ thể ghi vào hợp đồng khi TV1 triển khai, các bên đọc cùng một bản.
- Bộ cấp I dùng chung trong một lượt day. Reserve mọi ID fixture trước khi cấp mới, tiếp tục sau hậu tố lớn nhất đã nạp/phát, kể cả ID của cá thể đã mất. Gather độc lập reserve ID từ hold fixture. Xuất file theo ID nhưng hold nội bộ vẫn theo thứ tự nhặt.
- TV1 chọn biểu diễn nội bộ đủ chính xác ở ngưỡng 30 và floor, bàn giao helper trước khi TV2/TV3 triển khai hao tươi. Gợi ý PRD dùng 240 đơn vị/điểm cho fixture biểu diễn chính xác. Giá trị fresh hữu hạn bất kỳ trong [0,100] vẫn phải được xử lý đúng, tránh làm tròn fixture vào nhánh khác.
- TV3 gọi hao tươi/giữ lại trước nấu; TV4 tiêu đúng cá thể TV3 đã giữ và chốt giá một lần. Món đang nấu/chín dùng base_price đã chốt, nguyên liệu thô đã tiêu rời stock.
- TV2/TV3 sửa các đoạn validate theo mode của mình. TV4 sửa điều phối day. Khi đụng scenario.py hoặc QuanSim, chủ lát ghép phần người còn lại trước khi đẩy commit chung.
- Bật contract_version 1.2 khi cả gather, quan và day đã dùng schema mới. Nếu hỗ trợ hai phiên bản nội bộ trong lúc chuyển, bộ đọc file chọn schema theo version. Chạy v1.2 phải từ chối kho đếm bằng mã 2.

### Thứ tự tích hợp và mốc giờ

| Phút | Việc và người chịu trách nhiệm |
|---|---|
| 0–7 | TV1 chốt schema/helper/ID; TV2–TV5 chuẩn bị fixture/test/UI song song. Cả nhóm ghi tác động lên file/test theo bảng trên. TV1 giao adapter đầu tiên để các lát ghép. |
| 7–20 | TV2 ghép gather, TV3–TV4 ghép quan/day, TV5 ghép HUD. Mỗi chủ lát sửa fixture count → cá thể, reserved count → ID và kỳ vọng giá theo độ tươi, ghi rõ lý do test thay đổi. |
| 20 | TV1 và TV5 chạy smoke giao file thật sau một bước cập bến, đối chiếu snapshot quán tick 0. Standup 2–3 phút, hỗ trợ lát trễ. |
| 20–25 | Hoàn thiện giữ lại sau ươn, giá và ID xuyên ngày. TV1 ghép bản hoàn chỉnh và bật v1.2 khi các đầu đã sẵn sàng. |
| 25–32 | TV5 chạy file/day/regression trên main. TV1 chốt CHANGELOG breaking change, TV2–TV4 đưa bằng chứng của mình. Hoàn thiện verification và log AI/làm rõ. |
| 32–35 | Dự phòng. TV5 cùng TV1 kiểm commit bàn giao trên main fork và đẩy tag phase-3 trước mốc lab 2:30. |

### Checklist nghiệm thu chung

Các mã AC-P3 dưới đây do nhóm đặt để truy vết yêu cầu TICKET-03.

- **AC-P3-01 · TV1** schema cá thể hợp lệ, mã 2 cho kho đếm/id trùng/kind lạ/fresh NaN, vô hạn hoặc ngoài miền, ghi kho nguyên tử và tick_limit giữ file.
- **AC-P3-02 · TV2** fresh=30 ươn ngay bước gather đầu, event đúng tick/ID/location, hàng mới chưa hao trong bước nhận, LIFO đúng payload cá thể.
- **AC-P3-03 · TV3** kho gồm phần giữ cùng hao, phát spoiled trước thử giữ lại, đủ hàng thì thay phần giữ, thiếu thì unfulfillable, đơn xử lý đúng thứ tự.
- **AC-P3-04 · TV4** fresh trung bình và floor đúng khi bắt đầu nấu, boa tính từ giá mới, món chín giữ giá, cook_started.items đúng thứ tự.
- **AC-P3-05 · TV1 + TV4 + TV5** file và day giữ đúng id/kind/fresh qua chuyển pha, không hao hai lần, ID tiếp tục xuyên ngày/đồ đã dùng, Shop/pause không hao.
- **AC-P3-06 · TV5** HUD, regression còn hiệu lực, log bằng chứng khớp commit và docs/verification/phase-3.md. TV1 cập nhật CHANGELOG, các thành viên cập nhật clarify/AI log theo phần mình.

### Mở rộng

Kỳ vọng một mục mở rộng của nhóm 5 người tính trên cả lab. Khi lõi và bàn giao đã ổn, trưởng nhóm kiểm mục mở rộng đã có bằng chứng và quyết định còn cần bổ sung gì. Nếu chọn current hoặc reservations thì ghi người nhận, extensions, test và bằng chứng trước khi bắt đầu.
