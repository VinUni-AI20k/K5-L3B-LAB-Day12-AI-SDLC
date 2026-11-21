# Specification Quality Checklist: Phase 1 lõi (gather + quan)

**Purpose**: Kiểm chất lượng spec trước plan · **Created**: 2026-11-21 · **Feature**: [spec.md](../spec.md)

## Content Quality
- [x] Không chi tiết cài đặt thừa (chỉ nhắc tên sự kiện/trường JSONL vì đó là Test Contract)
- [x] Tập trung giá trị người chơi / test chấm
- [x] Mục bắt buộc đã đủ

## Requirement Completeness
- [x] Không còn `[NEEDS CLARIFICATION]` (đã thay bằng `GIẢ ĐỊNH`, ghi `docs/clarify.md` #12–#22)
- [x] FR kiểm được, AC-P1-01…23 đều có cách kiểm headless
- [x] Success criteria đo được
- [x] Edge case đã liệt kê
- [x] Phạm vi rõ (không đồ họa, không `day`)
- [x] Giả định và phụ thuộc ghi rõ

## Feature Readiness
- [x] Mỗi FR có AC
- [x] User story phủ luồng chính gather, kho, quan

## Notes
- Rủi ro chính: giả định thứ tự bước và luật quan chưa được PO xác nhận với PRD-0 (không đọc được bằng AI).
