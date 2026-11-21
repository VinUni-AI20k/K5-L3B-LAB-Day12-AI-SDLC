# Kế hoạch Phase 1 (≤ 1 trang)

> Thời gian: 0:00 – 1:00 (hạn tag `phase-1` trước 1:00).
> Mục tiêu cốt lõi: Hoàn thành lõi luật Gather và Quán, đạt chuẩn Test Contract v1.0, chạy được headless và giao tiếp qua file kho.

## 1. Mục tiêu
- **Gather (`sim/gather`)**: Di chuyển, oxy/ngạt/ngất, cơ chế hái và bắt cá, cập bến, xuất kho nguyên tử.
- **Quán (`sim/quan`)**: Nấu ăn, phục vụ khách, tính tiền/uy tín, đọc kho từ buổi sáng.
- **Tích hợp**: Hợp đồng kho khớp schema mục G; smoke test 2 tiến trình thành công; tính tất định (deterministic) 100%.

## 2. Việc / Người / Phụ thuộc

| Thành viên | Module / Trách nhiệm | Việc chính | Phụ thuộc |
|---|---|---|---|
| **Người 1** | `sim/gather` + PO | Lát 1 (bơi, oxy, ngạt, ngất LIFO); Lát 2 (hái nút, bắt cá, giỏ đầy, cập bến); giữ `docs/clarify.md` | Độc lập; cung cấp kho cho Người 2 |
| **Người 2** | `sim/quan` + Integrator | Lát 3 (khách, gọi món, kiên nhẫn); Lát 4 (bếp, nấu, trả tiền, uy tín); kiểm `scenario.py`; chốt hợp đồng và gắn tag | Nhận file kho từ Người 1 |
| **Người 3** | `client/ui` + Scrum | Khung UI, HUD tối thiểu (thời gian, oxy, máu, giỏ, kho); setup repo, `AGENTS.md`, retro | Đọc snapshot từ `Session` của Người 1 & 2 |
| **Người 4** | `qa` + QA Lead | Viết test độc lập, kiểm tra tất định (`cmp`), ma trận truy vết `docs/verification/phase-1.md` | Kiểm sau khi Người 1 & 2 hoàn thành lát |

## 3. Danh sách AC cốt lõi
- **AC-P1-01 -> AC-P1-05**: Bơi qua biên `dive`/`surface`, oxy (-1/+6), `oxygen_empty`, ngạt `choke` t+59, ngất `faint` bỏ giỏ LIFO.
- **AC-P1-06 -> AC-P1-11**: Giỏ trần `hold_capacity`, hái nút `ready` gần nhất (hồi 1200 ticks), bắt cá (yield, hồi 30 ticks), xử lý giỏ đầy `hold_full`.
- **AC-P1-12 -> AC-P1-15**: Cập bến xét trước hái, hết giờ `time` giữ giỏ, xuất kho đúng schema, tính tất định byte-matching.

## 4. Rủi ro & Giảm thiểu
- **Quá tải lát 1+2**: Tách làm 2 lát rõ ràng, viết test unit theo từng lát, chốt clarify sớm.
- **Lệch schema kho**: Dùng chung `inventory.py`, kiểm chứng qua smoke test hai tiến trình ngay sau khi xong lát 2.
- **Sai ca biên (t+59, mép bán kính)**: Viết test scenario bao phủ các giá trị biên thay vì chỉ test tay.

