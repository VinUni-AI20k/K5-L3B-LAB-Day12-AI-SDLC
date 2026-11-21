# Specification Analysis Report — 002-day-loop (speckit-analyze, chỉ đọc)

| ID | Loại | Mức | Vị trí | Tóm tắt | Khuyến nghị |
|---|---|---|---|---|---|
| B1 | Phụ thuộc / tiến độ | HIGH | tasks P0 | Lõi P1 chưa code (hái, bắt cá, toàn bộ quán) mà mọi AC-P2 quán/day và regression dựa vào | P0 làm ngay phút 0–20; TV3/TV4 chưa sang lát 3 khi P0 quán chưa xanh |
| B2 | Constitution VI / phạm vi | HIGH | plan Complexity | v1.1 buộc sửa 7 file khung (research phase-2 §3) và vỡ test cũ `test_smoke_p1.py:45, :70-77` | Chủ: TV1 (`contract`, `inventory` — T211), TV6 (`headless, inputs, scenario, runner, live` — T240–T245, T248); TV5 sửa test có lý do (T251) |
| B3 | Ambiguity | LOW (đã giảm) | spec Clarifications | Bản đề đầy đủ đã chốt `"1.1"`, `"paused"`, `cause:"monster"`, `"days_complete"`, `{}`, 6 s. Còn: vị trí hit (P2-Q7), `attack` chưa bật (P2-Q6), `faint` do ngạt (P2-Q3) | GIẢ ĐỊNH trong spec; PO ghi clarify (T254) |
| B4 | Inconsistency | MEDIUM | T203 vs `GatherSim.try_add_hold` | `try_add_hold` thêm từng món; bắt cá cần "đủ chỗ cho cả đàn" | Thêm hàm thêm theo lô (kiểm chỗ trước) — ghi trong T203 |
| B5 | Inconsistency (đã sửa) | LOW | specs/001 contracts/events.md | `hold_full` `{source_id}` lệch `docs/contracts` `{kind}` | Đã đổi specs/001 sang `{kind}` |
| B6 | Coordination | HIGH | tasks lát 4 + UI | TV6 vừa PO, vừa chủ 5 file khung, vừa chủ UI Cursor | TV5 pair T245; Cursor làm UI theo task; lát (1) xong sớm thì TV1 đỡ T242 |
| B7 | Phụ thuộc | LOW | T260–T266 | UI cần `live.py --mode day` | Đã thêm T248 (TV6) |
| B8 | Ambiguity | LOW | FR-203 | Tên luồng RNG và việc không reset theo Ngày là GIẢ ĐỊNH | Chốt ở `docs/contracts/` v1.1 |

## Độ phủ
| Nhóm | Số | Có task |
|---|---|---|
| FR-201…214 | 14 | 14 (100%) |
| AC-P2-01…31 | 31 | 31 (100%): 01 T210/T216 · 02 T207/T251 · 03–07 T216 · 08–14 T224 · 15, 18–28 T247 · 16–17 T233 · 23, 25, 29, 30 T252 · 31 T250 |
| Task không gắn AC | — | T254, T255, mở rộng (đề xuất) |

**Metrics**: 14 FR · 31 AC · 45 task (+2 đề xuất mở rộng) · CRITICAL 0 · HIGH 3 · MEDIUM 1 · LOW 4 · `[NEEDS CLARIFICATION]` 0.
**Kết luận**: Không CRITICAL → implement được; B1 (lõi P1 chưa code), B2 (sửa khung) và B6 (TV6 quá tải) quyết định có kịp tag `phase-2` lúc 1:55.
