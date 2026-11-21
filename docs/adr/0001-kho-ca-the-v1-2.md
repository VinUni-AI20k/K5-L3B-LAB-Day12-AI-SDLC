# ADR-0001: Đổi kho đếm theo loại sang kho cá thể (Contract v1.2, TICKET-03)

- Trạng thái: **đề xuất** — chờ cả nhóm chốt ở phút 0–7 Phase 3 (TV6 dẫn, TV1 quyết kỹ thuật/hợp đồng)
- Ngày, người đề xuất: 2026-11-21, TV6 (thanhhale288)

## Bối cảnh
TICKET-03 thay kho `{"items":{kind: n}}` bằng mảng cá thể `{"items":[{"id","kind","fresh"}]}`, thêm độ tươi (giỏ −0.5/s, kho quán −0.25/s, ươn khi `fresh < 30`), giữ chỗ theo id và giá theo độ tươi. Ở v1.2, file kho đếm phải trả mã 2. Đề: `docs/prd/phase-3-ticket-03.md`.

## Các lựa chọn đã cân nhắc
1. **Đổi một lần (big bang):** mọi module đổi cùng lúc rồi bật v1.2. Rủi ro: `main` hỏng giữa chừng, khó tích hợp với 4 lát song song.
2. **Adapter trước, hai phiên bản nội bộ, bật v1.2 sau cùng:** `inventory.py` đọc/ghi được cả hai schema theo `contract_version`; các sim chuyển dần sang cá thể; đổi `contract_version` thành `"1.2"` khi gather (ghi) và quan (đọc) đều sẵn sàng. Đề gợi ý cách này.

## Quyết định (đề xuất)
- Chọn **lựa chọn 2**.
- Độ tươi lưu dạng **số nguyên 240 đơn vị/điểm** (giỏ −2/tick, quán −1/tick), chỉ đổi ra số thực khi xuất JSONL/file. Lý do: so ngưỡng 30 chính xác, không sai số float.
- Id `I1, I2, …` do một bộ cấp id duy nhất xuyên pha và Ngày (dùng `IdAllocator`).
- Ghi `--inventory-out` bằng file tạm cùng thư mục rồi `os.replace` (nguyên tử), đúng một lần khi có `gather_end`.
- Thứ tự tích hợp: (1) adapter + contract `freshness` → (2) Lặn, Quán, HUD song song → (3) day → (4) bật `"1.2"`, smoke, regression, `CHANGELOG.md`.

## Hệ quả — bảng tác động
| Module | File cần đổi | Test bị ảnh hưởng | Người |
|---|---|---|---|
| Adapter / schema | `chonoi/inventory.py`, `chonoi/contract.py`, `chonoi/scenario.py`, `chonoi/headless.py`, `game.contract.json` | Thêm: kho đếm → mã 2, id trùng, `fresh` ngoài [0,100], ghi nguyên tử | TV1 (+ TV6 phần khung) |
| Lặn | `chonoi/sim/gather.py` | Thêm: ngưỡng 30 (scenario mẫu → `spoiled` tick 1), rơi LIFO cá thể | TV2 (+TV1) |
| Quán | `chonoi/sim/quan.py` | Thêm: giữ lại khi vừa ươn, chốt `base_price`; đổi: test giá/boa cũ (ghi lý do) | TV3 (giữ chỗ), TV4 (hao tươi, giá) |
| day | `chonoi/runner.py`, `chonoi/sim/day.py` | Thêm: bàn giao cùng tick, id xuyên Ngày | TV6 (agent khung) |
| HUD | `chonoi/web/index.html` | `tests/test_live.py` giữ xanh | TV6 (Cursor) |
| QA | `tests/`, `docs/verification/phase-3.md`, `docs/proof/phase-3/`, `CHANGELOG.md` | Regression P1–P2 còn hiệu lực | TV5 |

Bảng chi tiết theo code hiện tại (file:hàm, test file:dòng): `docs/research/phase-3.md` (agent research đang viết).
