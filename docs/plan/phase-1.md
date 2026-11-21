# Kế hoạch Phase 1 (0:00 – 1:00)

## Mục tiêu
- Hoàn thành phạm vi lõi PRD-0 Phase 1: Buổi sáng (`gather`: bơi, lặn, oxy, ngạt, ngất, giỏ, hái rau, bắt cá, cập bến, xuất kho) và Buổi tối (`quan`: khách, giữ chỗ, nấu, bưng, phục vụ, tiền, uy tín).
- Đảm bảo tính tất định từng byte qua headless (60 tick/s, seed qua `Streams`).
- Smoke test hai tiến trình độc lập (`gather --inventory-out` -> `quan --inventory`) thành công trên `main`.
- Đầy đủ tài liệu SDLC và gắn tag `phase-1` trước 1:00.

## Phân công việc & Phụ thuộc
| Việc | Người làm | Phụ thuộc | Trạng thái |
|---|---|---|---|
| Chốt hợp đồng kho, sự kiện & cập nhật `docs/contracts/README.md`, `docs/clarify.md` | Le Quy Toan (ToanLee5433 - Integrator) | PRD-0 | Hoàn thành |
| Cập nhật `TEAM.md`, `game.contract.json`, kiểm tra `tools/check_team.py` | Dư Văn Hùng (czx04 - QA lead) | Danh sách nhóm | Hoàn thành |
| Lát 1 + Lát 2 (`sim/gather.py`): Bơi, oxy, ngạt, máu, ngất, hái cây, bắt cá, dock, ghi kho | Le Quy Toan (ToanLee5433) | `docs/contracts/` | Hoàn thành |
| Lát 3 + Lát 4 (`sim/quan.py`): Khách hàng, giữ chỗ, nấu bếp B1, phục vụ bàn T1, tiền & uy tín | Nguyễn Thành Nam (Ishodayo - PO) / Dư Văn Hùng (czx04) | Hợp đồng kho | Đang thực hiện |
| Giao diện trực tiếp (`client/ui`, `live.py` / HUD) | Đàm Hồng Thái (itsbra1vo - Scrum/Release) | Snapshot sim | Đang thực hiện |
| Bộ test kiểm chứng, ma trận truy vết `docs/verification/phase-1.md` | Dư Văn Hùng (czx04 - QA lead) | Tất cả các lát | Đang thực hiện |
| Tích hợp, merge PR vào `main` và gắn tag `phase-1` | Le Quy Toan (ToanLee5433 - Integrator) | Smoke test pass | Chờ tích hợp |

## Rủi ro & Giải pháp
1. **Rủi ro sai lệch snapshot/event schema giữa gather và quan**:
   - Giải pháp: Khóa chặt hợp đồng tại `docs/contracts/README.md` theo đúng PRD-0 mục E, F.
2. **Rủi ro đọc/ghi file kho giữa hai tiến trình**:
   - Giải pháp: Ghi file tạm cùng thư mục rồi `os.replace` (atomic write); kiểm tra đúng schema `{"items": {...}}` loại bỏ giá trị 0.
3. **Rủi ro lệch thời gian / không kịp tag phase-1**:
   - Giải pháp: Kiểm tra chéo ở phút 45, chạy smoke test hộp đen tự động, chuẩn bị sẵn tài liệu kiểm chứng.
