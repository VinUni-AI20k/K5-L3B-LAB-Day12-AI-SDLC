# Kế hoạch Phase 1 (≤ 1 trang)

> Người viết: TV6 (PO · Scrum/Release · UI). Nguồn: PRD-0 trên lab board + starter (`game.contract.json`, các `TODO(nhóm)`). Hạn tag `phase-1`: **trước 1:00**.

## Mục tiêu
- Buổi sáng `gather` đúng luật: oxy giảm dưới nước / hồi ở mặt nước, ngạt mỗi 60 tick mất 1 Máu, Máu 0 thì ngất mất cả giỏ; hái nút ở mặt nước, bắt cá dưới nước, giỏ 12 món LIFO, cập bến hoặc hết giờ thì ghi kho.
- Buổi tối `quan` đúng luật: khách đến theo lịch, kiên nhẫn 60 s, nấu, bưng 1 món, ăn 10 s, tiền + boa 20%, uy tín 0–5.
- Nối được: `gather --inventory-out kho.json` → `quan --inventory kho.json`.
- Headless tất định (cùng seed → JSONL giống từng byte); test xanh; tag `phase-1` chạy được.
- **Không** làm đồ họa / sáng tạo trong Phase 1 (lõi đúng trước).

## Việc / người / phụ thuộc
| Việc | Người | File | Phụ thuộc | Mốc |
|---|---|---|---|---|
| Tóm AC PRD-0, bấm giờ kickoff, plan, thỏa thuận nhóm | TV6 | `TEAM.md`, `docs/plan/` | — | 0:15 |
| Chốt hợp đồng: schema kho, sự kiện, giao diện sim↔UI; `team_size = 6` | TV1 | `docs/contracts/`, `game.contract.json` | — | 0:15 |
| Gather lát 1: oxy, ngạt, Máu, ngất, giỏ LIFO, dive/surface/oxygen_empty/choke/faint | TV1 | `chonoi/sim/gather.py` | hợp đồng | 0:45 |
| Gather lát 2: hái, mọc lại, bắt cá, hồi chiêu, hold_full, bến trước hái, kho | TV2 | `chonoi/sim/gather.py` | giỏ của TV1 (~0:25) | 0:45 |
| Quán: khách theo lịch, giữ chỗ, kiên nhẫn, bỏ đi, no_dish, kiểm scenario | TV3 | `chonoi/sim/quan.py`, `chonoi/scenario.py` | schema kho | 0:45 |
| Quán: bếp, một interact/tick, bưng, phục vụ, tiền, boa, uy tín | TV4 | `chonoi/sim/quan.py` | khách của TV3 (~0:35) | 0:45 |
| Unit test, ma trận AC, skill/hook #1, AGENTS.md | TV5 | `tests/`, `docs/verification/`, `.agents/skills/` | code TV1–TV4 | 0:55 |
| Hỏi Anh Năm → `clarify.md`; standup ~0:30; kiểm HUD bằng `chonoi.live`; gom nhật ký AI | TV6 | `docs/clarify.md`, `docs/standup.md`, `docs/ai-usage-log.md`, `chonoi/web/` | — | 0:55 |
| Tích hợp gather → kho → quan; tag | TV1 (+TV5 báo xanh) | — | tất cả | < 1:00 |

## Rủi ro
- Hai người cùng sửa một file (`gather.py`, `quan.py`) dễ conflict → mỗi người một hàm riêng, pull trước khi sửa, commit nhỏ.
- 30' build quá ngắn → cắt theo AC, ưu tiên phần test ẩn chấm; ngừng thêm tính năng ở 0:45.
- Sai thứ tự một bước (PRD mục 13.8 / mục F) làm lệch JSONL → TV5 so chuỗi sự kiện với PRD.
- Test ẩn kiểm lại phase trước → lỗi Phase 1 bị trừ ở mọi phase sau.
- Dùng `random`/đồng hồ hoặc hard-code số → chỉ dùng `Streams` và đọc `game.contract.json`.
- Có thành viên chưa commit/chưa có dòng trong `TEAM.md` → TV6 kiểm `git shortlog -sn` ở 0:50.
