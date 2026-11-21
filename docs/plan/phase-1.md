# Kế hoạch Phase 1

Hoàn thiện luồng sáng đi hái, bắt cá và tối mở quán. Kiểm chứng hai mode headless và việc chuyển kho từ `gather` sang `quan` theo Test Contract v1.0. Hạn tag `phase-1` là 1:00 tính từ lúc bắt đầu lab. [README](../../README.md)

| Phần việc | Người phụ trách | Phụ thuộc và điểm bàn giao |
|---|---|---|
| Gather lát 1 — oxy, ngạt, Máu, ngất và giỏ | Lead / Integrator | Hái và bắt cá gọi chung `_add_to_hold`. [PR #1](https://github.com/justapea25/K5-L3B-LAB-Day12-AI-SDLC-MATH/pull/1) |
| Gather lát 2 — hái, mọc lại, bắt cá | Developer lát 2 | Nối vào `gather.py`, dùng helper giỏ và xuất nguyên liệu theo schema kho. [Khung tích hợp](https://github.com/justapea25/K5-L3B-LAB-Day12-AI-SDLC-MATH/pull/2) |
| Quán lát 3 — khách, gọi món, giữ chỗ, bỏ đi | Developer lát 3 | Thống nhất trạng thái khách và cách bàn giao nguyên liệu giữ chỗ với lát 4. [Schema khách](../contracts/customer.md) |
| Quán lát 4 — nấu, bưng, phục vụ, trả tiền | Developer lát 4 | Nhận kho từ `gather`, dùng chung schema khách và tên sự kiện với lát 3. [Kho mẫu](../contracts/inventory.sample.json), [sự kiện](../contracts/events.md) |
| QA và bằng chứng | QA lead | Chạy test công khai và test các lát trên commit tích hợp. Ghi kết quả thực tế. [Ma trận](../verification/phase-1.md) |
| Docs và harness AI | Nguyễn Xuân Khánh Linh (@linkiewinkie) | Cập nhật hướng dẫn agent, nhật ký AI và câu hỏi cần đối chiếu với PRD-0. [Clarify](../clarify.md), [AGENTS.md](../../AGENTS.md) |

QA cần kiểm tra luồng khách cùng lát 3 và lát 4 vì hai lát cùng sử dụng nguyên liệu giữ chỗ. Lead chạy lại test sau khi gộp, đối chiếu bằng chứng với commit gắn tag và ghi rõ hạng mục còn thiếu nếu tới hạn.
