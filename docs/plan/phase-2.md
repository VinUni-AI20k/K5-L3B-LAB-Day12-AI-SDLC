# Kế hoạch Phase 2 (re-planning, Ticket-02, 1:00–1:55)

Người ghi: Võ Hồng Lương (D, Integrator). Nguồn: Ticket-02 trên lab board (số mục dưới đây là số mục trong Ticket-02). Trạng thái từng việc ở Google Sheet phân công, tab "Phân công" (dòng P2-xx). Bản này không chép lại số liệu của đề; số liệu chuẩn chỉ nằm trong `game.contract.json` (v1.1) sau việc P2-02.

## Mục tiêu

Hết 1:55 có `phase-2` chạy được, `contract_version: "1.1"`: số chuẩn mới (mục 1.1, 1.3), Cá Sấu và Máu (1.2), 2 bếp 4 bàn 6 món (1.3), `--mode day` với kế hoạch D1–D5, Shop, pause, menu và HUD (mục 2), smoke tích hợp có bằng chứng, hồi quy Phase 1 còn hiệu lực, `docs/verification/phase-2.md` khớp commit gắn tag.

## Quyết định

1. **Schema kho giữ nguyên** (`{"items": {kind: số nguyên}}`, mục 4.1: `day` bàn giao theo schema v1.0 trong bộ nhớ). Thêm hai nguyên liệu `ca_keo` và `keo_neo` vào danh sách hợp lệ của `chonoi/inventory.py`. File `chonoi/inventory.py` là file khóa: sửa có chủ ý, báo cả nhóm.
2. **Hai chế độ `gather` và `quan` vẫn chạy độc lập** như v1.0; `day` chỉ ghép chúng. Không đổi hành vi một chế độ để phục vụ `day`.
3. **Thứ tự chuyển pha trong `day`** (mục 2 và 4.5): `day_start` → `day_plan` → `phase_start(gather)` → … `gather_end` → `phase_start(quan)` cùng tick → … `quan_end` → `phase_start(shop)` cùng tick → `shop_end` → Ngày kế (hoặc `end` với `days_complete`). Pha mới chỉ chạy gameplay từ bước sau.
4. **`invuln_ticks` theo `contract_version`:** v1.0 từ chối trong scenario, v1.1 chấp nhận (mục 4.3). Giữ cả hai hành vi và có test cho mỗi bản; kiểm theo `contract_version` đọc từ `game.contract.json`.
5. **Thứ tự tích hợp để `main` luôn chạy được:** (a) P2-02 contract 1.1 vào `main` trước, đi kèm sửa test Phase 1 bị lệch số (ghi lý do); (b) các lát gather, quán, Cá Sấu, Shop làm song song ở file riêng; (c) `day.py` dựng bằng fixture từ sớm, ghép thật sau smoke phút 20; (d) UI chỉ đọc snapshot.
6. **Mở rộng (mục 3) là tùy chọn;** nhóm 4 người không bắt buộc. Chỉ làm khi lõi đã đúng, tắt được ở headless.

## Phân tích tác động

| Module | File cần đổi | Test bị ảnh hưởng | Người phụ trách |
|---|---|---|---|
| Contract và schema | `game.contract.json`, `chonoi/contract.py` (đổi ràng buộc: 8 đàn cá, 6 món, 2 bếp, 4 bàn, `day_plan`, `shop`, `gather.monsters`), `chonoi/inventory.py` (thêm 2 nguyên liệu), `chonoi/scenario.py` (khóa mới: `day`, `monsters`, `fish[].age_ticks`, `invuln_ticks`, `attack_cd_ticks`) | `tests/test_scenario_contract.py` và các test quán giả định một bàn T1; `chonoi/contract.py` hiện bắt buộc đúng 6 đàn cá nên `validate_tuning` phải đổi cùng lúc với contract; `tests/test_smoke_p1.py` | D |
| Gather: cá bơi và sinh | `chonoi/sim/gather.py` | `tests/test_gather_rules.py`, `tests/test_gather_prd.py` (đàn cá mặc định đứng yên nay bơi; test dùng `random_fish: false` thì không đổi) | A |
| Gather: Cá Sấu, Máu | `chonoi/sim/monsters.py` (mới), một lời gọi trong `gather.py` | thêm `tests/test_p2_monsters.py` | C |
| Quán chuẩn | `chonoi/sim/quan.py` | `tests/test_quan_slice3.py`, `tests/test_quan_slice4.py`, `tests/test_quan_rules.py`: các test dùng `tuning_with_tables` thêm T2, T3 sẽ trùng id với 4 bàn mới; test "một bàn" cần viết lại theo 4 bàn | B (viết lại test: người sửa luật) |
| Shop | `chonoi/sim/shop.py` (mới) | thêm `tests/test_p2_shop.py` | A |
| Chế độ `day` | `chonoi/sim/day.py` (mới), `chonoi/runner.py`, `chonoi/headless.py`, `chonoi/inputs.py` (nút `pause`, `shop_done`, `attack`, `photo`, chuỗi `buy`) | `tests/test_smoke_p1.py` (`--mode day` đang bị từ chối ở v1.0), `tools/smoke_phase1.py` | D |
| UI | `chonoi/web/index.html`, `chonoi/live.py` (menu, pause, HUD, Shop) | `tests/test_live.py` | C |
| Tài liệu | `docs/contracts/README.md` (sự kiện mới: `monster_hit`, `fish_spawned`, `day_start`, `phase_start`, `paused`, `resumed`, `bought`, `buy_failed`, `shop_end`), `docs/verification/phase-2.md` | không | D |

`runner.py`, `headless.py`, `inputs.py`, `live.py`, `web/` là khung của giảng viên: chỉ sửa chỗ cần, báo cả nhóm và ghi lý do trong commit.

## Việc, người, phụ thuộc (mã AC theo Sheet)

| AC | Việc | Người | Phụ thuộc |
|---|---|---|---|
| AC-P2-01 | P2-02: contract 1.1 và số chuẩn; sửa test Phase 1 lệch số | D | không (làm trước) |
| AC-P2-02 | P2-03: cá bơi, sinh cá (mục 1.1) | A | AC-P2-01 |
| AC-P2-03 | P2-04: Cá Sấu, Máu, ngạt (mục 1.2) | C | AC-P2-01 |
| AC-P2-04 | P2-05: quán 2 bếp 4 bàn 6 món (mục 1.3) | B | AC-P2-01 |
| AC-P2-05 | P2-06: Shop nâng cấp oxy và Máu (mục 2) | A | AC-P2-02 |
| AC-P2-06 | P2-07: `--mode day`, pause, input mới (mục 2, 4) | D | AC-P2-01 |
| AC-P2-07 | P2-08: menu, pause, HUD (mục 2) | C | AC-P2-03, AC-P2-06 |
| AC-P2-08 | P2-09: smoke tích hợp ở phút 20 | D | AC-P2-02, AC-P2-04 |
| AC-P2-09 | P2-10 đến P2-13: hồi quy Phase 1, bằng chứng, retro, tag | D | tất cả |

Lịch: phút 0–5 re-planning (bản này), 5–20 build và P2-02 vào `main`, phút 20 smoke `gather --inventory-out` → `quan --inventory`, 20–35 build tiếp và chốt luồng `day`, 35–45 smoke `day --days 1` và hồi quy Phase 1, 45–50 retro, 50–55 dự phòng; `phase-2` chậm nhất 1:55.

## Rủi ro

- **D là điểm nghẽn:** giữ contract, `day`, smoke và tag. Nếu P2-07 trễ, đẩy fixture `day` cho A hoặc B để tích hợp sớm.
- **Số liệu chuẩn chép sai:** mọi số chuẩn lấy trực tiếp từ Ticket-02, đối chiếu lại từng số khi làm P2-02; không dùng số nhớ.
- **Hồi quy Phase 1 lệch số:** ví dụ 4 bàn làm các test "một bàn" sai; sửa test phải kèm lý do trong commit và trong `docs/verification/phase-2.md`.
- **Xung đột file:** A (`gather.py`) và C (`monsters.py` gọi từ `gather.py`) sửa gần nhau; C chỉ thêm một lời gọi ở bước theo thứ tự xử lý mục 4.5.
- **Nhóm 4 người, đề kỳ vọng nhiều hơn:** chấp nhận chưa làm mở rộng; ghi trung thực trong README và bằng chứng.
- **Vẫn nợ từ Phase 1:** tiền tố id khách ngẫu nhiên (`docs/clarify.md` câu 6); commit và hồ sơ của B và C.

## Câu hỏi cho PO / `docs/clarify.md`

- Tiền tố id khách ngẫu nhiên khi chưa nạp khách nào (câu 6, còn mở).
- Khi làm P2-02, ghi thêm vào `docs/clarify.md` mọi chỗ Ticket-02 chưa nói rõ (ví dụ Cá Sấu M2, M3 theo Ngày, giá trị mặc định của `day` khi thiếu khóa).
