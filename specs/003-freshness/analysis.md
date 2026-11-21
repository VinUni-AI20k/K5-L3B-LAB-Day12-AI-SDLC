# Specification Analysis Report — 003-freshness (speckit-analyze, chỉ đọc)

| ID | Loại | Mức | Vị trí | Tóm tắt | Khuyến nghị |
|---|---|---|---|---|---|
| C1 | Phụ thuộc | HIGH | spec Phụ thuộc, tasks cảnh báo | P3 xây trên P1/P2 chưa xong (hái/bắt cá TODO, quán chưa nối `step`, `day` chưa chạy, contract v1.0) → AC-P3-11…17, 19–21 chưa thể xanh | Giữ P0 của 002 trước; Lặn/adapter P3 làm được ngay |
| C2 | Phạm vi khung | HIGH | plan Complexity | Đụng 5 file khung (`inventory, contract` TV1; `scenario, headless, runner` TV6) | Một chủ mỗi file, adapter trước, báo nhóm, CHANGELOG |
| C3 | Chính xác số | MEDIUM | FR-309, R1–R2 | Float ở ngưỡng 30 và `floor` giá dễ lệch | Số nguyên 240 đơn vị/điểm; test AC-P3-07/08/16 ở biên |
| C4 | Underspec | MEDIUM | spec Clarifications | Tên trường trạng thái đơn (`order_status`/`unfulfillable`) và payload món chưa có trong đề | TV1 chốt ở `docs/contracts/` (T304) |
| C5 | Ambiguity | LOW | contracts/inventory-v1.2 | Độ chính xác ghi file và id nạp không dạng `I<n>` | GIẢ ĐỊNH ghi float đầy đủ; tiếp tục từ max `I<n>` + 1 |
| C6 | Coordination | MEDIUM | tasks Phase 4–5 | TV6 vừa PO, khung (T305, T306, T330, T331), vừa HUD | Agent khung làm T305/T306/T330/T331; Cursor làm HUD; TV6 duyệt |
| C7 | Coverage | LOW | — | Mở rộng current/reservations không có AC | Đúng phạm vi: tùy chọn, sau lõi |

## Độ phủ
| Nhóm | Số | Có task |
|---|---|---|
| FR-301…310 | 10 | 10 (100%) |
| AC-P3-01…23 | 23 | 23 (100%): 01–05 T307 · 06–10 T313 · 11–17 T325 · 18 T341 · 19–21 T332 · 22–23 T342 |
| AC bắt buộc theo brief | 7 | kho đếm → 2 (03), ghi nguyên tử (05), spoiled tick 1 (08), thử giữ lại (13–14), chốt base_price (16), bàn giao day (19), smoke file (18) |

**Metrics**: 10 FR · 23 AC · 30 task · CRITICAL 0 · HIGH 2 · MEDIUM 3 · LOW 2 · `[NEEDS CLARIFICATION]` 0.
**Kết luận**: Không CRITICAL. Thứ tự: adapter → lát song song → day → bật v1.2. C1 quyết định khả năng đạt tag `phase-3` lúc 2:30.
