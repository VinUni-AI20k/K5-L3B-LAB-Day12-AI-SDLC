# Kế hoạch Phase 1

Đích bàn giao là hai ca chơi được, HUD đủ trường, smoke test truyền kho qua hai tiến trình và tag `phase-1` trên `main` trước phút 60. Kế hoạch dùng starter Python và preset hiện tại. Điền tên, GitHub handle, vai và người dự phòng vào [TEAM.md](../../TEAM.md) khi kickoff.

## Bốn lát và phạm vi file

| Người / vai | Việc giao cho agent | File được sửa | Bằng chứng riêng |
|---|---|---|---|
| **1 · PO** | Bơi, biên, oxy, ngạt, ngất và sức chứa giỏ. Sở hữu thứ tự bước Gather và nối hàm người 2. Hỏi PO lab khi luật mơ hồ. | `chonoi/sim/gather.py`, `tests/test_p1_gather_player.py`, `docs/clarify.md` | Chạm oxy 0 ở tick t, ngạt ở t+59. Nổi đúng tick ngạt. Ngất làm rơi đồ LIFO và xuất kho rỗng. |
| **2 · Scrum/Release** | Hái, bắt, mọc lại và kiểm tra đường xuất kho có sẵn. Hoàn thiện HUD hai ca trong client mặc định, dùng kho mẫu và fixture để thử độc lập. | `chonoi/sim/gather_resources.py` (mới), `chonoi/web/index.html`, `tests/test_p1_gather_resources.py`, `README.md` | Đúng mép bán kính và hòa theo ID, đầy giỏ không mất đàn/nút, cập bến/hết giờ giữ đúng hàng. Bằng chứng chơi thử và HUD hai ca. |
| **3 · QA lead** | Dựng khách fixture, lịch khách, chọn món theo seed, giữ chỗ, kiên nhẫn và xử lý khách đang chờ rời bàn. Kiểm dữ liệu scenario và chạy smoke nối kho. | `chonoi/sim/quan_customers.py` (mới), `chonoi/scenario.py`, `tests/test_p1_quan_customers.py`, `docs/verification/phase-1.md` | Kiểm hết món, hết chỗ, chọn món tất định, nhả giữ chỗ, fixture mâu thuẫn trả mã 2 trước khi ghi. |
| **4 · Integrator** | Di chuyển quán, tương tác bếp/bàn, nấu, bưng, phục vụ, thu tiền, boa, đóng ca. Sở hữu thứ tự bước Quán và nối hàm người 3. Review, tích hợp, chạy lại trên `main` và đẩy tag. | `chonoi/sim/quan.py`, `tests/test_p1_quan_service.py`, `TEAM.md`, `AGENTS.md`, metadata nhóm trong `game.contract.json` sau khi báo nhóm | Nấu → bưng → phục vụ → trả tiền. Thử phục vụ đúng tick hết kiên nhẫn hoặc đóng ca, kiểm boa, tiền, uy tín và điểm. |

Mỗi người ghi bằng chứng vào `docs/proof/phase-1/nguoi-N/` và phản tư vào `docs/members/<handle>.md`. Mỗi người gửi thông tin sử dụng AI cho **người 1** cập nhật `docs/ai-usage-log.md`. Người 2 tổng hợp retro vào `docs/retro.md`. Người 4 theo dõi hai skill, hook hoặc command tự viết theo `AGENTS.md` và ghi lại cách dùng. Review chéo **1 ↔ 2** và **3 ↔ 4**.

## Chạy song song và tích hợp

1. **0–15 phút** — Chốt [giao diện tích hợp](phase-1-integration.md) trên cùng commit gốc. Mỗi người dùng một clone hoặc Git worktree riêng và một nhánh `p1/gather-player`, `p1/gather-resources`, `p1/quan-customers` hoặc `p1/quan-service`. Giao agent đúng hàng trong bảng, kèm PRD mục F/G và giao diện tích hợp. Người 1 và 4 có thể gửi commit nối hàm riêng sau commit triển khai để review dễ hơn.
2. **15–45 phút** — Người 2 và 3 dùng fixture trong test để gọi hàm trực tiếp. Người 1 và 4 chỉ nối import ở nhánh của mình sau khi đồng bộ module tương ứng. Thử xuất kho thật trước phút 25. Mỗi agent chạy test và ghi kết quả vào bằng chứng hoặc mô tả commit.
3. **45–55 phút** — Tích hợp và kiểm từng cặp 1+2, 3+4. Gộp vào `main` khi đã qua test. Người 3 chạy smoke, đối chiếu ma trận và lưu log. Người 2 chơi thử hai ca, hoàn thiện README với cách chạy từ clone sạch tối đa 3 lệnh, phím, điểm và lệnh test.
4. **55–60 phút** — Người 4 chạy lại test trên commit bàn giao, xác nhận bằng chứng gắn đúng commit và đẩy tag `phase-1`. Ghi rõ tiêu chí chưa đạt nếu còn. Mốc tối thiểu 3 commit có nội dung mỗi người tính trên cả buổi lab.

Nếu cần sửa file của người khác hoặc đổi chữ ký đã chốt, báo chủ file và Integrator để chủ file thực hiện. Người 4 điều phối sửa khung dùng chung khi có lỗi contract đã tái hiện, thông báo nhóm và ghi lý do.
