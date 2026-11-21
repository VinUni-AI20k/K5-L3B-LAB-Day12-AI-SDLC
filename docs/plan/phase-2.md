# Kế hoạch Phase 2 · Một ngày ở chợ nổi

Đích bàn giao là vòng ngày chơi được, Test Contract v1.1, regression Phase 1 theo luật còn hiệu lực và tag `phase-2` trên `main` trước mốc 1:55. Dùng starter Python, giữ nhóm 4 người và làm phần lõi. Điền tên và GitHub handle tương ứng trong [TEAM.md](../../TEAM.md) khi kickoff.

## Bốn lát và quyền sửa file

| Người / nhánh | Phần làm và tiêu chí | File phụ trách |
|---|---|---|
| **1 · PO** · `p2/fish-data` | **AC-P2-01, 02.** Dữ liệu chuẩn v1.1 và 6 nguyên liệu. Cá khởi tạo, bơi, đổi hướng, phản xạ và sinh theo seed. Là đầu mối hỏi khách hàng và cập nhật clarify. | `game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py`, `chonoi/sim/gather_resources.py`, `tests/test_p2_fish_data.py`, `tests/test_p1_gather_resources.py`, `docs/clarify.md`, `docs/ai-usage-log.md` |
| **2 · Scrum/Release** · `p2/gather-monsters` | **AC-P2-03, 07.** Bố trí Cá Sấu theo Ngày, chase/recoil/hit, bất tử, rơi đồ, ngất. Sở hữu vòng Gather và nối module tài nguyên đang đứng riêng ở Phase 1. Sở hữu loader scenario dùng chung. | `chonoi/sim/gather.py`, `chonoi/sim/gather_monsters.py` (mới), `chonoi/scenario.py`, `tests/test_p2_gather_monsters.py`, `tests/test_p2_scenario.py`, `docs/retro.md` |
| **3 · QA lead** · `p2/quan-ui` | **AC-P2-04, 05, 09.** Quán 2 bếp/4 bàn, menu 6 món, lọc theo kế hoạch Ngày, trả dữ liệu cho HUD. Hoàn thiện **client** menu, màn chuyển ca, Shop, pause và HUD; dùng snapshot mẫu để làm trước. Chạy kiểm chứng, sửa fixture Quán cũ theo PRD và tổng hợp ma trận. | `chonoi/sim/quan.py`, `chonoi/sim/quan_customers.py`, `chonoi/web/index.html`, `tests/test_p2_quan.py`, `tests/test_p1_quan_service.py`, `tests/test_p1_quan_customers.py`, `docs/verification/phase-2.md` |
| **4 · Integrator** · `p2/day-shop` | **AC-P2-06, 07, 08.** Tính kế hoạch, điều phối vòng Ngày, Shop, pause và tick. Sở hữu điểm vào headless và backend live. Dùng fixture hai ca ngắn để tích hợp sớm, chạy lại trên `main` và gắn tag. | `chonoi/sim/day.py`, `chonoi/sim/shop.py` (mới), `chonoi/runner.py`, `chonoi/inputs.py`, `chonoi/headless.py`, `chonoi/live.py`, `tests/test_p2_day.py`, `tests/test_live.py`, `tests/test_smoke_p1.py`, `tests/test_python_starter_units.py`, `AGENTS.md`, `TEAM.md`, `README.md` |

Người 1 là người duy nhất ghi manifest. Người 2, 3 và 4 gửi phần dữ liệu hoặc validation mình phụ trách theo [giao diện v1.1](phase-2-integration.md). Người 2 nhận yêu cầu liên quan đến loader scenario; kiểm tra nghiệp vụ tại thời điểm dựng ca nằm ở sim tương ứng. Nếu cần đổi file ngoài lát, nhờ chủ file thực hiện và báo Integrator. Báo nhóm trước khi sửa manifest/hợp đồng, hoặc sửa khung starter và ghi lý do.

## Đồng bộ và bàn giao

- **Phút 0–5** — Chọn chung một commit gốc, báo nhóm các thay đổi v1.1 và kiểm tra tag `phase-1` trên fork. Mỗi người dùng clone/worktree và nhánh riêng. Review chéo **1 ↔ 2**, **3 ↔ 4**. Người 1 ưu tiên commit manifest và bộ nạp v1.1 cùng nhau. Người 4 ưu tiên gửi giao diện live để người 3 dựng UI bằng dữ liệu mẫu.
- **Phút 5–20** — Người 1 thử cá bằng fixture; người 2 thử quái bằng fixture tắt cá động; người 3 thử Quán độc lập với kho có sẵn; người 4 thử chuyển pha bằng ca ngắn. Có thể đồng bộ commit dữ liệu khi đã sẵn sàng, và nối module trước ở nhánh tích hợp để kiểm cả cặp.
- **Phút 20** — Người 3 và 4 chạy smoke hai tiến trình `gather → quan`, lưu `docs/proof/phase-2/integration.*`. Standup 2–3 phút; người đã xong có thể nhận một file test hoặc bằng chứng chưa có chủ, sau khi báo chủ lát.
- **Phút 20–35** — Nối Gather, Quán và Day theo chữ ký; thử ca ngất mở Quán với kho rỗng. Người 3 nối client với backend live và chơi thử Shop/pause. Gộp lát qua review và test.
- **Phút 35–45** — Trên `main`, chạy hồi quy P1, smoke `day --days 1`, nhiều Ngày và kiểm hiệu năng/HUD. Người 3 ghi ma trận, người 4 gắn tag tại commit bàn giao.
- **Phút 45–55** — Người 2 ghi retro và người nhận hành động. Chừa thời gian xử lý lỗi, ghi trung thực các AC chưa đạt và đẩy tag trước 1:55. Mỗi người lưu bằng chứng dưới `docs/proof/phase-2/nguoi-N/`, cập nhật phản tư riêng và gửi thông tin dùng AI cho người 1.

Căn cứ triển khai và kiểm chứng nằm ở [Ticket 02](../../PHASE2.md), [giao diện tích hợp](phase-2-integration.md) và [ma trận nghiệm thu](../verification/phase-2.md).
