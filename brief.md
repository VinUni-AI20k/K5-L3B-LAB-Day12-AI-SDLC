# Brief Phase 2 & Phase 3 — chia việc theo người

> Người viết: TV6 (thanhhale288, PO · Scrum/Release). Cập nhật: 2026-11-21, sau sync `main` @ `2fd94cf`.
> Đề đầy đủ (chép từ lab board để AI đọc được): [`docs/prd/phase-2-ticket-02.md`](docs/prd/phase-2-ticket-02.md), [`docs/prd/phase-3-ticket-03.md`](docs/prd/phase-3-ticket-03.md).
> Spec & task chi tiết: [`specs/002-day-loop/tasks.md`](specs/002-day-loop/tasks.md) (45 task), [`specs/003-freshness/tasks.md`](specs/003-freshness/tasks.md) (30 task). Research: [`docs/research/phase-2.md`](docs/research/phase-2.md), [`docs/research/phase-3.md`](docs/research/phase-3.md). Quyết định đổi kho: [`docs/adr/0001-kho-ca-the-v1-2.md`](docs/adr/0001-kho-ca-the-v1-2.md).

## Ai là ai

| Vai | Người (theo commit — **(suy luận)**, mỗi người tự điền `TEAM.md`) | Module |
|---|---|---|
| TV1 | thanhanbk02 | `sim/gather` lát 1, Integrator (contract, tag) |
| TV2 | Hải Đăng (`tangnguyenhaidang`) | `sim/gather` lát 2 |
| TV3 | dqk2210 | `sim/quan` khách, giữ chỗ, uy tín |
| TV4 | noobpyno (`mai-le-ba-vuong`) | `sim/quan` bếp, bưng, tiền, boa |
| TV5 | (chưa rõ) | `qa`, QA lead |
| TV6 | thanhhale288 | `client/ui`, PO · Scrum/Release, khung `day` |

> ⚠️ `TEAM.md` mới có dòng TV6. Commit của người không có trong `TEAM.md` **không được tính** — mỗi người tự điền tên + handle ngay (`python3 tools/check_team.py`).

## Tóm tắt đề

**Phase 2 — TICKET-02 "Một ngày ở chợ nổi" (Contract v1.1, hạn tag `phase-2` 1:55).** Hai buổi thành một vòng Ngày: DayIntro → gather → EveningIntro → quan → DayResult → Shop. Số chuẩn mới (180 s mỗi buổi, oxy 30 s, Máu 3, giỏ 12, N1–N6, cá bơi 1.5 m/s và sinh thêm). Cá Sấu: chạm ≤ 1.5 m khi người chơi ở d ≥ 10 → −1 Máu, rơi một nửa giỏ theo LIFO, bất tử 90 tick. Quán 2 bếp, 4 bàn, 6 món; boa `floor(giá × 0.2)`; bếp lấy đơn theo `order_tick`. Mode mới `--mode day --days 1..5`, Shop nâng cấp oxygen/hp, pause.

**Phase 3 — TICKET-03 "Mùa Nước Nổi" (Contract v1.2, hạn tag `phase-3` 2:30) — đổi yêu cầu.** Kho thành **cá thể** `{"items":[{"id":"I1","kind":"ca_linh","fresh":100}]}`; kho đếm cũ → **mã 2**. Độ tươi: giỏ −0.5/s, kho quán −0.25/s, `fresh < 30` là ươn (vẫn chiếm ô, không nấu, phát `spoiled` đúng 1 lần). Giữ chỗ theo id (tươi nhất trước). Giá = `floor(giá × fresh trung bình / 100)`. Ghi file kho nguyên tử.

**Mở rộng:** nhóm 6 người cần **≥ 2 mục** trong cả buổi lab, khai trong `extensions` + README. Đề xuất: `burn` (TV4) và `snake` (TV2), làm sau lõi.

## Hiện trạng `main` (`2fd94cf`, 60 test OK)

| Hạng mục | Tình trạng |
|---|---|
| Gather lát 1 + 2 | ✅ trên `main` (TV1 `4d2752c`, TV2 PR #2) |
| Quán | 🟡 QuanSim (PR #1) đã gộp nhưng **chưa nối vào `step`**; `dqk2210/quan-validate` (TV3) và `mai-le-ba-vuong` (TV4) **chưa gộp** |
| Contract | 🔴 vẫn `"1.0"` → `--mode day` trả mã 2 "chờ TV1" |
| Mode `day`, Shop, pause, live day (TV6) | ✅ `2fd94cf` (chạy được ngay khi contract lên v1.1) |
| UI menu/màn ngày/Shop/pause/HUD + HUD độ tươi (TV6) | ✅ chờ dữ liệu sim thật |
| Tag | 🔴 **chưa có `phase-1`, `phase-2`** |

## Chia việc Phase 2 (ưu tiên: push code đang có, gắn tag đúng giờ, ghi trung thực)

### TV1 — thanhanbk02
- [ ] **Gắn `phase-1` ngay** (quá hạn), rồi `phase-2` trước 1:55 sau khi TV5 báo xanh.
- [ ] T210/T211: dán JSON tuning v1.1 từ [`docs/research/phase-2.md`](docs/research/phase-2.md) vào `game.contract.json` (`contract_version:"1.1"`), cập nhật `contract.py`/`inventory.py` (thêm `ca_keo`, `keo_neo`, `fish_initial: 8`). **Việc này mở khóa mode `day`.**
- [ ] Lát 1: số chuẩn + cá bơi/sinh (`fish_speed`, `fish_spawn_ticks` 360, trần 12).

### TV2 — Hải Đăng
- [ ] Lát 2: Cá Sấu patrol/chase/recoil, hit, rơi LIFO `floor(n/2)`, bất tử 90 tick, ngất (`faint` có `cause:"monster"`, `lost`, `hp:0`).
- [ ] T246: `GatherSim` nhận ngữ cảnh Ngày (`oxygen_max`, `hp_max` theo `active_upgrades`; M2 từ Ngày 3).
- [ ] (sau lõi) mở rộng `snake`.

### TV3 — dqk2210
- [ ] **Gộp `dqk2210/quan-validate` vào `main` ngay** (đụng `chonoi/scenario.py` mà TV6 cũng sửa — gộp sớm đỡ conflict).
- [ ] Nối luật khách vào `QuanSim.step`: lịch 120 + 900·k nếu có bàn trống, ghế trống id nhỏ nhất, kiên nhẫn 3.600 tick, `no_dish`, uy tín −0.5 khi bỏ đi.
- [ ] T230: lọc món theo `day_plan` (mode `day`), 4 bàn.

### TV4 — noobpyno
- [ ] **Gộp `mai-le-ba-vuong` vào `main`**, nối 4 hàm thao tác QuanSim vào `step`.
- [ ] 2 bếp, 6 món; bếp lấy đơn `reserved` cũ nhất theo `order_tick` rồi id bàn; boa `floor`, uy tín +0.2.
- [ ] (sau lõi) mở rộng `burn`.

### TV5 — QA lead
- [ ] T251: sửa test cũ vỡ khi contract lên v1.1, **ghi lý do trong commit**: `test_smoke_p1.py:45, :65-67, :70-77`, `test_python_starter_units.py:46-50`.
- [ ] Smoke tích hợp `gather --inventory-out → quan --inventory`, lưu `docs/proof/phase-2/integration.*`; smoke `day --days 1`.
- [ ] Điền `docs/verification/phase-2.md` (AC-P2-xx → bằng chứng → kết quả, trung thực).
- [ ] Skill nhóm tự viết #1 trong `.agents/skills/` (Spec Kit không tính).

### TV6 — thanhhale288
- [x] Spec 002, research P2, UI menu/DayIntro/EveningIntro/DayResult/Shop/Summary/pause/HUD (chữ ≥ 18 px).
- [x] Lát 4: mode `day`, Shop, pause, `live.py --mode day` (T240–T245, T248).
- [x] Retro nháp P2 (`docs/retro.md`), `docs/clarify.md` theo số chuẩn, nhật ký AI.
- [ ] Hỏi Anh Năm clarify #30, #32, #33.

## Chia việc Phase 3 (đổi kho sang cá thể + độ tươi)

**Phút 0–7, cả nhóm:** chốt [ADR-0001](docs/adr/0001-kho-ca-the-v1-2.md) — adapter trước, đọc được 2 phiên bản, bật `"1.2"` khi hai đầu sẵn sàng; độ tươi **số nguyên 240 đơn vị/điểm** (giỏ −2/tick, quán −1/tick; research đã chứng minh float ươn sớm 1 tick ở bước 8400 thay vì 8401). Ghi breaking change vào `CHANGELOG.md`.

**Thứ tự tích hợp:** (1) adapter + contract `freshness` → (2) Lặn, Quán, HUD song song → (3) `day` → (4) bật `"1.2"`, smoke, regression → tag.

| Module | File | Test | Người |
|---|---|---|---|
| Adapter / schema | `inventory.py`, `contract.py`, `game.contract.json` | kho đếm → mã 2, id trùng, `fresh` ngoài [0,100] | **TV1** |
| Adapter (khung) | `scenario.py`, `headless.py`, `runner.py` | ghi nguyên tử, bộ cấp id toàn cục | TV6 (agent khung) |
| Lặn | `sim/gather.py` | ngưỡng 30 (`spoiled` tick 1), LIFO cá thể | **TV2** (+TV1) |
| Quán — giữ chỗ | `sim/quan.py` | giữ theo id, thử giữ lại khi vừa ươn | **TV3** |
| Quán — hao tươi, giá | `sim/quan.py` | hao 0.25/s, `base_price` theo fresh | **TV4** |
| day | `runner.py`, `sim/day.py` | bàn giao cùng tick, id xuyên Ngày | TV6 (agent khung) |
| HUD | `chonoi/web/index.html` | `test_live.py` xanh | TV6 (Cursor) |
| QA | `tests/`, `docs/verification/phase-3.md`, `docs/proof/phase-3/`, `CHANGELOG.md` | regression P1–P2 | **TV5** |

### TV1
- [ ] T301–T304: schema kho v1.2 trong `inventory.py` (đọc theo `contract_version`, kho đếm → mã 2), thêm `tuning.freshness` `{initial:100, gather_decay_per_s:0.5, quan_decay_per_s:0.25, spoiled_below:30}` (JSON sẵn trong [`docs/research/phase-3.md`](docs/research/phase-3.md)).
- [ ] Đổi `contract_version:"1.2"` khi gather + quan sẵn sàng. Gắn `phase-3` trước 2:30.

### TV2
- [ ] Cá thể trong giỏ, id `I1, I2…` tăng xuyên pha/Ngày; hao từ bước sau khi lấy; `spoiled` đúng 1 lần theo id.
- [ ] Rơi hàng/ngất theo LIFO cá thể; `lost` là mảng cá thể.
- [ ] Xong khi: `{"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":30}],"random_fish":false,"monsters":[]}}` chạy 1 bước → `spoiled` ở tick 1.

### TV3
- [ ] Giữ chỗ lấy cá thể tươi nhất (hòa theo id); `customers[].reserved` là mảng id.
- [ ] Phần giữ vừa ươn: nhả hết, thử giữ lại 1 lần (theo `order_tick` rồi id bàn), thiếu → `unfulfillable`.

### TV4
- [ ] Kho quán hao 0.25/s kể cả hàng đang giữ; pause dừng hao; món chín không hao.
- [ ] Bắt đầu nấu: tiêu đúng id đang giữ, `base_price = floor(giá × fresh TB / 100)`; boa trên giá đã chốt; `cook_started.data.items` sắp theo kind rồi id.

### TV5
- [ ] Test ngưỡng 30, thử giữ lại khi vừa ươn, chốt giá, bàn giao file (smoke của đề: `fresh:100`, `interact` frame 0, `quan --inventory <file> --ticks 0`).
- [ ] Phút 20: smoke kho; cuối: smoke 2 tiến trình + `day`, regression P1–P2; 8 test sẽ vỡ liệt kê trong research P3.
- [ ] `docs/verification/phase-3.md`, `docs/proof/phase-3/`, `CHANGELOG.md`; skill nhóm #2.

### TV6
- [x] Spec 003, research P3, ADR-0001 (bảng tác động), HUD độ tươi (T335), clarify #34–#45.
- [ ] Agent khung: T305, T306, T330, T331 (đang làm; không sửa `inventory.py` của TV1).
- [x] Cursor: T336 (nguyên liệu món đang nấu, giá chốt).
- [ ] Dẫn standup phút 20, retro bài học đổi kho, nhật ký AI.

## Điểm đồng bộ & git

- **Handoff P3:** TV1 chốt schema kho → TV2, TV3, TV4, TV6 mới đổi code theo schema.
- **File dễ conflict:** `gather.py` (TV1 + TV2), `quan.py` (TV3 + TV4), `scenario.py` (TV3 + TV6). Mỗi người một hàm riêng, `git pull --rebase` trước khi sửa, commit nhỏ, gộp branch sớm.
- **Chỉ TV1** sửa `game.contract.json`, `docs/contracts/` và gắn tag (sau khi TV5 báo xanh).
- **TV6 giữ** `docs/clarify.md`, `docs/standup.md`, `docs/ai-usage-log.md`. Câu hỏi đề gửi PO.
- **Mỗi người tự làm:** dòng của mình trong `TEAM.md`, `docs/members/<handle>.md`, ≥ 3 commit có nội dung bằng tài khoản của mình.

## Rủi ro & câu hỏi còn mở

- 🔴 Chưa có tag nào; contract còn v1.0; quán chưa chạy trong `step`. Test ẩn kiểm lại phase trước.
- 🟡 Hai branch quán chưa gộp, đụng `scenario.py`.
- Hỏi Anh Năm: #30 (ngất do ngạt có `lost`/`hp`?), #32 (`extensions` mảng hay object), #33 (đàn bị bắt biến mất?), #34 (`freshness` ở `tuning` hay gốc), #37, #40, #42 — xem [`docs/clarify.md`](docs/clarify.md).
