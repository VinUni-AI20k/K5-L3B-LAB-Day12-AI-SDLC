# Specification Analysis Report — 001-phase-1-core (speckit-analyze, chỉ đọc)

| ID | Loại | Mức | Vị trí | Tóm tắt | Khuyến nghị |
|---|---|---|---|---|---|
| A1 | Constitution (V) | HIGH | spec Clarifications, FR-014…FR-022 | Luật quan + thứ tự bước là GIẢ ĐỊNH vì PRD-0 không đọc được bằng AI | PO (T003) đối chiếu PRD-0 mục E/F/13.8 trước 0:30; sửa spec trước code |
| A2 | Ambiguity | MEDIUM | FR-014, data-model lịch khách | Chưa nói rõ khách "đến ở tick 120" là tick của dòng event (k+1) hay bước k | Chốt: dòng `customer_arrived` có `tick == first_customer_tick + k·interval` (đếm sau khi tăng tick) |
| A3 | Constitution / phạm vi | MEDIUM | plan Complexity, T019 | AC-P1-23 có thể cần sửa `chonoi/scenario.py` (file khung, Q-F) | Mặc định kiểm trong `QuanSim.__init__`: đã kiểm `runner.py:78-80` dựng Session trước khi mở JSONL → không để lại file (research mục 2.1 nói ngược — cần sửa research) |
| A4 | Ambiguity | MEDIUM | FR-009, R4/R5 | Nhặt một phần / cá biến mất ảnh hưởng `fish_caught` và test ẩn | Xác nhận clarify #5, #6 (gốc) |
| A5 | Underspec | MEDIUM | contracts/events.md (Q-D) | `data` của sự kiện mới (`choke{hp}`, `hold_full{source_id}`…) chưa khóa | TV1 chốt ở `docs/contracts/` (T002) |
| A6 | Underspec | LOW | data-model Player | `invuln_ticks` không dùng ở P1 | Ghi rõ "chỉ đếm ngược" (đã ghi) |
| A7 | Coordination | LOW | tasks T004/T005 | Hai người cùng file `gather.py`/`quan.py` | Đã tách hàm + checkpoint 0:25/0:35 |

## Độ phủ

| Nhóm | Số | Có task | Ghi chú |
|---|---|---|---|
| FR | 26 | 26 (100%) | FR-024…026 phủ qua T019/T027/T028–T031 |
| AC-P1 | 23 | 23 (100%) | 01–05 T010 · 06–10 T013 · 11–12 T015 · 14–16, 23 T020 · 17–21 T025 · 13, 22 T027 |
| Task không gắn yêu cầu | — | T034, T035 (T037 golden phủ hồi quy) | Việc quy trình (harness, nhật ký) — hợp lệ |

**Metrics**: 26 FR · 23 AC · 37 task · CRITICAL 0 · HIGH 1 · MEDIUM 4 · LOW 2 · `[NEEDS CLARIFICATION]` còn lại 0.

**Kết luận**: Không có CRITICAL → có thể bắt đầu implement; nhưng A1 phải được PO xử lý sớm (sai giả định quan = trượt test ẩn ở mọi phase).
