# Bảng công việc Phase 1 (0:00–1:00)

**Quy ước:** đợt 1 làm ngay, đợt 4 làm cuối. Task nào ghi "Chờ" thì phải đợi task đó xong rồi mới làm. Trong lúc chờ, làm tiếp task khác của mình ở đợt thấp hơn.

| Đợt | Mã task | Người | Module | Việc cần làm | Chờ ai / task nào | Ai chờ mình |
|---|---|---|---|---|---|---|
| **1** (0:00, làm ngay) | M6.1 | F (cả nhóm cùng) | M6 | Điền `TEAM.md`, sửa `team_size: 6`, chốt hợp đồng (trường, sự kiện, schema kho) | Không | **Tất cả** (chặn mọi task .2) |
| 1 | M6.2 | F | M6 | Đọc PRD-0, ghi `clarify.md`, hỏi giảng viên | Không | Cả nhóm (khi có câu mơ hồ) |
| 1 | M1.1 | A | M1 | Spec: AC bơi, oxy, ngạt, Máu, ngất, biên | Không | M1.2 |
| 1 | M2.1 | B | M2 | Spec: AC hái, bắt cá, giỏ LIFO, cập bến, kho | Không | M2.2 |
| 1 | M3.1 | C | M3 | Spec: AC khách, giữ chỗ, kiên nhẫn | Không | M3.2 |
| 1 | M4.1 | D | M4 | Spec: AC bếp, bàn, bưng, tiền, tip, uy tín | Không | M4.2 |
| 1 | M5.1 | E | M5 | `AGENTS.md`, 2 skill/hook, `ai-usage-log.md` | Không | Không ai |
| **2** (sau khi M6.1 xong, ~0:15) | M1.2 | A | M1 | Viết test/scenario từ AC | M1.1, M6.1 | M1.3 |
| 2 | M2.2 | B | M2 | Viết test: hái, `node_regrown`, `hold_full`, cooldown, kho | M2.1, M6.1 | M2.3 |
| 2 | M3.2 | C | M3 | Viết test: lịch khách, `no_dish`, rời đi | M3.1, M6.1 | M3.3 |
| 2 | M4.2 | D | M4 | Viết test: nấu, phục vụ, tip, uy tín | M4.1, M6.1 | M4.3 |
| 2 | M5.2 | E | M5 | Danh sách trường UI đọc / lệnh gửi | M6.1 | M5.3 |
| 2 | M6.3 | F | M6 | `scenario.py` kiểm mâu thuẫn + test | M6.1 | Test của M3, M4 |
| **3** (~0:25–0:45) | M1.3 | A | M1 | Code: `dive`/`surface` (**làm trước**), oxy, ngạt, Máu, ngất | M1.2 | M2.3b, M5.4, M6.4 |
| 3 | M2.3a | B | M2 | Code: giỏ LIFO, cập bến, ghi kho (độc lập, làm trước) | M2.2 | M2.3b |
| 3 | M3.3 | C | M3 | Code: dựng khách từ scenario, giữ chỗ, kiên nhẫn | M3.2 | M3.4, M4.4 |
| 3 | M4.3 | D | M4 | Code: interact bếp/bàn, nấu, bưng, tiền, uy tín (dùng khách giả) | M4.2 | M3.4, M4.4 |
| 3 | M5.3 | E | M5 | HUD gather và quán trên `chonoi.live` | M5.2 | M5.4 |
| 3 | M2.3b | B | M2 | Code: hái ở mặt nước, bắt cá dưới nước | M2.2, **M1.3 (A)** | M2.4 |
| **4** (~0:45–1:00, cuối phase) | M1.4 | A | M1 | Chạy test, ghi bằng chứng | M1.3 | M6.5 |
| 4 | M2.4 | B | M2 | Chạy test, đối chiếu `inventory.sample.json`, bằng chứng | M2.3a, M2.3b | M6.5 |
| 4 | M3.4 | C | M3 | Ghép khách ↔ bếp, bằng chứng | M3.3, **M4.3 (D)** | M6.5 |
| 4 | M4.4 | D | M4 | Ghép bếp ↔ khách, chạy test, bằng chứng | M4.3, **M3.3 (C)** | M6.5 |
| 4 | M5.4 | E | M5 | Chạy thử `chonoi.live`, chụp ảnh | M1.3, M2.3, M3.3, M4.3 | M6.5 |
| 4 | M6.4 | F | M6 | Test tích hợp gather → kho → quán; cùng seed → output giống từng byte | M1.3, M2.3, M3.3, M4.3 | M6.5 |
| 4 | M6.5 | F (PO) | M6 | Duyệt M1–M5 theo checklist, điền `verification/phase-1.md` | Bằng chứng M1.4–M5.4, M6.4 | M6.6 |
| 4 | M6.6 | F | M6 | Chạy toàn bộ test, **gắn tag `phase-1`** | M6.5 | — |

## Việc ngoài bảng (mọi người, mọi phase)

| Việc | Khi nào |
|---|---|
| Mỗi người ≥3 commit có nội dung, PR nhỏ ≤400 dòng | Suốt phase |
| Review chéo: A↔B, C↔D, E↔F (nhận xét bám diff) | ~0:40–0:50 |
| Dòng của mình vào `ai-usage-log.md` và `standup.md` | Cuối phase |
| Bị vướng quá 10 phút: nói ngay trong kênh nhóm, người dự phòng nhận việc | Bất cứ lúc nào |

## Ba điểm dễ nghẽn

1. **M6.1 (hợp đồng)** phải xong trong 15 phút đầu, vì 6 task đợt 2 đều chờ nó.
2. **A làm phần `dive`/`surface` trước** trong M1.3 để B làm được M2.3b.
3. **C và D trao đổi sớm** về trạng thái khách (chờ → ngồi → ăn → rời), để ghép ở đợt 4 không phải sửa lại.
