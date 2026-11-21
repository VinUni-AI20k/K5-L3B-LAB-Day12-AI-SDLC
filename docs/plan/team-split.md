# Chia việc 5 người — Day 12 (Quán Ăn Chợ Nổi)

> **DRAFT, chưa commit.** Đọc kèm `docs/plan/phase-1-rules.md`.
> Trạng thái repo lúc viết: fork `PH31M/K5-L3B-LAB-Day12-AI-SDLC-MMMMV`, 2 commit starter, chưa có tag,
> `TEAM.md` còn trống, `team_size = 4` (sai, phải là 5), `chonoi/sim/{gather,quan}.py` còn `TODO(nhóm)`.

## 1. Nguyên tắc chia

1. **Mỗi người sở hữu một file/vùng file** — không ai sửa file người khác, tránh conflict trong 3 giờ.
2. **Mỗi phase mỗi người có ít nhất 1 commit có nội dung** → tự khắc đạt mốc ≥ 3 commit/người.
3. **Không push thẳng vào file của người khác**; sửa `game.contract.json`/`tests/helpers.py` chỉ qua Integrator.
4. Số liệu chỉ đọc từ `game.contract.json`; ngẫu nhiên chỉ qua `Streams`; test xanh mới được gắn tag.

## 2. Vai + vùng file

| # | Người | Handle | Vùng file sở hữu | Vai quy trình | Tải |
|---|---|---|---|---|---|
| 1 | Nguyễn Cao Minh | `caominhnguyen05` | `chonoi/sim/gather.py` (thứ tự tick, oxy, ngạt, ngất, giỏ) · P2: `chonoi/sim/quan_service.py` | **Integrator**: `game.contract.json`, merge, gắn tag | 7 |
| 2 | Trần Đình Nhật Minh | `trandinhnhatminh1452` | `chonoi/sim/gather_actions.py` (hái nút, bắt cá, cập bến) · P2: `chonoi/sim/quan_customers.py` | **PO**: đọc lab board, `docs/clarify.md`, `docs/plan/phase-n.md` | 7 |
| 3 | Tào Quang Vinh | `qvinhh2312` | `chonoi/web/index.html` + asset/âm thanh | **UX/Demo**: HUD, đồ họa, màn kết thúc, kịch bản demo 3 phút | 6 |
| 4 | Nguyễn Văn Minh | `vm140205-collab` | `tests/test_*.py`, `docs/proof/`, `docs/verification/` | **QA lead**: test theo PRD, chạy cổng, ma trận truy vết | 7 |
| 5 | Phạm Hoàng Đức Minh | `PH31M` | `TEAM.md`, `AGENTS.md`, `.agents/skills/`, `README.md` (mục Sáng tạo), `CHANGELOG.md`, fixtures `tests/fixtures/` | **Scrum/Release**: quyền repo, collaborator, tag + release `v1.0.0` | 6 |

**Tải** là điểm công ước (1 = 15 phút việc thật): gather core 3, gather actions 3, quán 3+3, UI 2+2, test 2+2,
ma trận+bằng chứng 2, quy trình+skill+release 2, sáng tạo/nội dung 1.5, retro+AI log 1.5, trực merge/gate 0.5.
Cân lại sau mỗi phase nếu ai lệch quá 1 điểm — người nhẹ nhận việc regression của người nặng.

Tên file P2 là **đề xuất tách** để hai người cùng làm `quan.py` mà không giẫm chân:
`QuanSim.step()` gọi helper trong `quan_customers.py` / `quan_service.py`. Nếu nhóm thấy thừa thì giữ 1 file,
nhưng khi đó **chỉ một người được sửa `quan.py` tại một thời điểm** và phải báo trước 1 phút.

## 3. Mốc giờ (3 giờ, đúng như README)

| Giờ | Mốc | Cổng bắt buộc trước khi sang mốc sau |
|---|---|---|
| 0:00–0:15 | Kickoff | 5 handle trong `TEAM.md`; `team_size = 5`; 5 issue (mỗi lát 1 issue); `docs/contracts/README.md` điền 3 mục; `PYTHONPATH=tests:. python3 -m unittest discover -s tests` xanh |
| 0:15–0:55 | Phase 1 code | **Cả hai buổi** (PRD §2): 4 lát song song + HUD; smoke 2 tiến trình; test mới xanh |
| 0:55–1:00 | **Tag `phase-1`** | `git status` sạch · test xanh · `docs/verification/phase-1.md` ghi trung thực cái chưa xong |
| 1:00–1:50 | Phase 2 | Mục mở rộng #1 của board + regression P1 + UI |
| 1:50–1:55 | **Tag `phase-2`** | test xanh + `gather → kho → quan` vẫn đúng |
| 1:55–2:25 | Phase 3 | Mục mở rộng #2 của board + regression P1/P2 |
| 2:25–2:30 | **Tag `phase-3`** | test xanh, không hồi quy phase trước |
| 2:30–2:55 | Phase 4 | Đóng băng tính năng: retro, `docs/members/<handle>.md` đủ 5, README "Sáng tạo của nhóm", `ai-usage-log` đủ dòng |
| 2:55–3:00 | **Tag `phase-4` + Release `v1.0.0`** | chạy lại toàn bộ từ tag `phase-1` → `phase-4` |

**Quy tắc thép:** đến mốc thì gắn tag ngay, kể cả khi còn dở — ghi thật vào `docs/verification/phase-n.md`.

## 4. Việc từng phase

### Phase 1 (0:00–1:00) — cả hai buổi, 4 lát song song (PRD §6.2)

| Người | Lát | File | Việc |
|---|---|---|---|
| Cao Minh | **1** + tích hợp | `chonoi/sim/gather.py` | dive/surface, oxy, ngạt (t+59), ngất LIFO, chặn interact khi ngất; điều phối merge |
| Nhật Minh | **2** + PO | `chonoi/sim/gather_actions.py` | chọn nút/cá (gần nhất, hòa theo `id_key`), hái, bắt (xóa đàn), hồi chiêu, `hold_full`, regrow; `docs/clarify.md` Q1–Q8 |
| Văn Minh | **3** + QA lead | `chonoi/sim/quan_customers.py` | khách đến theo `first_customer_tick`/`customer_interval_s`, giữ đúng công thức, kiên nhẫn, `customer_left`, `no_dish`; giữ ma trận truy vết |
| Đức Minh | **4** + release | `chonoi/sim/quan_service.py` | bếp (nấu, chốt giá, `ready_ticks`), bưng 1 món, phục vụ đúng `order_id`, `paid`, boa, uy tín, `quan_end` |
| Vinh | **HUD** | `chonoi/web/index.html` | HUD sáng (thời gian, oxy, máu, giỏ) + tối (kho, món gọi, kiên nhẫn, bếp, tay, tiền, uy tín); màn kết thúc |

PRD khuyến nghị đúng cách này: *"Nhóm 4 người có thể giao mỗi người một lát. Người thêm ở nhóm 5–6 có thể lo HUD, QA hoặc hỗ trợ lát đang chậm."*
Phút 20 rà lát vướng và điều người xong sang hỗ trợ.

Thứ tự phụ thuộc: lát 1 và 2 cùng đụng `GatherSim.step()` → **chỉ Cao Minh sửa `step()`**, Nhật Minh viết helper được gọi từ đó.
Tương tự lát 3 và 4: **chỉ Văn Minh sửa `QuanSim.step()`**, Đức Minh viết helper.

### Phase 2 (1:00–1:55) — mở rộng #1

Chốt nội dung tại 1:00 sau khi đọc board `#phase-2`. Phân công mặc định: mỗi người giữ module của mình,
thêm 1 mục mở rộng chia theo (a) luật, (b) UI, (c) nội dung/sáng tạo, (d) test + bằng chứng, (e) quy trình.
Bắt buộc có regression P1: hidden test chấm lại phase trước.

### Phase 3 (1:55–2:30) — mở rộng #2

Chốt nội dung tại 1:55. Giữ nguyên nguyên tắc: lõi đúng trước, sáng tạo sau, mọi thứ thêm phải tắt ở headless.

### Phase 4 (2:30–3:00) — đóng gói

Retro có số (commit/người, token/người, 1 lần AI sai), `docs/members/<handle>.md` ×5, README mục "Sáng tạo của nhóm",
`CREDITS.md` asset, `CHANGELOG.md`, release `v1.0.0`, kịch bản demo 3 phút.

## 5. Git: mỗi người một nhánh, PR theo phase

**Nhánh cố định cả buổi** (đỡ phải nhớ tên): `feat/cao-minh`, `feat/nhat-minh`, `feat/quang-vinh`, `feat/van-minh`, `feat/duc-minh`.
Mỗi phase: rebase `main` → push → mở **1 PR** → 1 người review → merge. Không ai push thẳng `main`.

**Vòng review** (không tự review mình, mỗi người review 1 PR/phase):

| PR của | Người review |
|---|---|
| Cao Minh | Đức Minh |
| Nhật Minh | Cao Minh |
| Quang Vinh | Nhật Minh |
| Văn Minh | Quang Vinh |
| Đức Minh | Văn Minh |

**Lịch PR trong mỗi phase** (T là mốc tag):

| Mốc | Việc |
|---|---|
| T−25′ | Mở PR, xong mô tả: AC nào, lệnh đã chạy, phần AI làm |
| T−20′ | Reviewer đọc diff + chạy `PYTHONPATH=tests:. python3 -m unittest discover -s tests`; comment bám diff |
| T−15′ | Merge theo thứ tự: **docs/team → gather core → gather actions → test → UI** |
| T−8′ | Trên `main`: chạy lại toàn bộ test + 1 lệnh headless thật |
| T−5′ | Integrator gắn tag; nếu còn PR chưa merge thì **tag trước**, PR đó sang phase sau |

PR ≤ ~400 dòng (mẫu PR đã có checklist). PR quá to thì tách theo commit — không tách nhánh.
Ghi vào mô tả PR: `Co-authored-by:` nếu làm cặp, để rubric "chia việc" thấy được.

- **Commit:** tiếng Việt, tiền tố `gather:`, `quan:`, `ui:`, `test:`, `docs:`, `chore:`; mỗi commit phải chạy được.
- **Trước khi mở PR:** `git fetch && git rebase origin/main` + test xanh; conflict tự sửa trong nhánh mình.
- **Không commit:** `*.jsonl`, `__pycache__`, file kho tạm (đã có `.gitignore`).
- **Định danh:** mỗi người `git config user.email` đúng email gắn với GitHub account của mình — commit sai email thì GitHub không gán cho handle, có thể bị tính là "ngoài danh sách".

## 6. Change request (điểm "đổi yêu cầu" của rubric 25đ nhóm)

Chọn **một** thay đổi thật, phát sinh từ chơi thử, ví dụ:
> "Một khách gọi 2 món → `carry_limit = 1` buộc phải bưng 2 chuyến, nhưng bàn chỉ giữ 1 khách nên không thể; đề xuất cho `hand` giữ 1 món + hạ `eat_s` hoặc cho phép đặt món trước."

Quy trình: issue → `docs/adr/0001-<slug>.md` (bối cảnh, lựa chọn, quyết định, **bảng tác động** file/test) → code → test → ghi vào `docs/verification/phase-2.md`. Không đổi schema kho, không đổi tên event đã công bố.

## 7. Bằng chứng phải nộp (map thẳng 100 điểm)

| Hạng mục | Điểm | File/bằng chứng |
|---|---|---|
| Test ẩn headless | 25 | chỉ có một cách: luật đúng PRD-0 + giữ nguyên schema/CLI |
| Làm việc nhóm | 25 | `TEAM.md`, issue, ≥3 commit/người, PR có review, ADR change request, `docs/standup.md` |
| Kiểm chứng | 15 | `docs/verification/phase-{1..4}.md` + `docs/proof/phase-n/` (JSONL, ảnh, lệnh đã chạy) |
| Harness AI | 10 | `AGENTS.md` sửa ở ≥3 phase, 2 skill `.agents/skills/`, `docs/ai-usage-log.md` |
| Retro | 10 | `docs/retro.md` có số + 1 lần AI sai |
| Chất lượng/sáng tạo | 10 | README "Sáng tạo của nhóm", tính năng thêm **tắt ở headless** |
| Demo | 5 | `docs/demo.md` (kịch bản 3 phút) + ảnh |

## 8. Rủi ro

| Rủi ro | Dấu hiệu | Xử lý |
|---|---|---|
| Yêu cầu phase 2–4 chỉ có trên lab board (không có trong repo) | codeánh đoán sai | PO đọc board tại 1:00/1:55/2:30, ghi AC vào `docs/plan/phase-n.md` **trước** khi code |
| Commit sai email/handle | GitHub không gán commit | kiểm `git log --format='%an <%ae>'` sau commit đầu tiên |
| Hai người sửa `quan.py` | conflict | tách file helper như mục 2, hoặc báo trước |
| Đổi `game.contract.json` làm lệch hidden test | test ẩn đỏ hàng loạt | chỉ Integrator sửa, chỉ `team`/`team_size` |
| Trễ tag | mất điểm phase | đặt báo thức 0:55/1:50/2:25; tag trước 5 phút |
| `faint`/`choke` sai thứ tự | test ẩn lệch tick | bám bảng thứ tự tick mục 1 của đặc tả |

## 9. 10 phút kickoff (làm đúng thứ tự)

1. Đức Minh thêm 4 người còn lại làm collaborator (Write), repo để public.
2. Điền `TEAM.md` theo bảng mục 2 + phần "Thỏa thuận" (kênh liên lạc, ai quyết khi bất đồng, ai gắn tag).
3. `game.contract.json`: `"team": "MMMMV"`, `"team_size": 5`.
4. `python3 tools/check_team.py` → phải in `OK: 5 thành viên`.
5. Mỗi người `git config user.email` đúng email GitHub **của mình**, commit một dòng vào `docs/standup.md` để kiểm định danh.
6. Tạo 5 issue theo mục 4 (mỗi người nhận 1).
7. Điền `docs/contracts/README.md`: schema kho (`docs/contracts/inventory.sample.json` đã có), 3 mục còn lại.
8. Tạo 5 nhánh `feat/<tên>`; chốt ai gắn tag (Integrator); chốt kênh báo khi kẹt > 10 phút (ai nhận việc của người vướng).
9. Chép 8 câu Q1–Q8 vào `docs/clarify.md` kèm giả định tạm.
10. Chạy baseline: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` → 32 test xanh (đã kiểm chứng).
