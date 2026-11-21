# UI sinh động theo PRD-0 Phase 1 — Implementation Plan (v2: làm trên nhánh)

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans. Steps dùng checkbox. Theo chỉ dẫn của user: TẠO NHÁNH MỚI + COMMIT CODE CHỜ LÊN NHÁNH TRƯỚC, rồi triển khai plan theo từng commit trên nhánh. KHÔNG push khi chưa được user đồng ý.

**Goal:** Nâng client `chonoi/web/index.html` từ "hình khối tạm" lên giao diện sinh động đúng PRD-0 mục 3 (miền Tây Nam Bộ): quán_states hoàn chỉnh (commit 2), reskin đề tài + animation (commit 3), thoại Nam Bộ + SFX (commit 4).

**Architecture:** Vẫn 1 file vanilla-JS canvas, chỉ ĐỌC `GET /state`, render phòng thủ. Hiệu ứng động dùng `sin(snap.tick)` (KHÔNG Math.random). Thoại/SFX là map event→hiển thị phía client, không đổi sim.

**Tech stack:** Vanilla JS + Canvas 2D, WebAudio oscillator (không asset ngoài), Python stdlib live server.

**Spec:** PRD-0 — mục 2 (HUD tối thiểu cả 2 buổi), mục 3 (phong cách: phù sa, dừa nước, nhà sàn, ánh hồng sớm; đèn dây vàng, khói bếp; Út Sen áo bà ba + khăn rằn + kính lặn + giỏ lưới; giọng Nam Bộ), mục 1 (tự do sáng tạo phải không đổi headless + ghi README "Sáng tạo của nhóm").

## Global Constraints
- Làm trên nhánh `feat/ui` (theo quy ước nhóm feat/gather, feat/qa). KHÔNG push khi chưa có sự đồng ý.
- Chỉ sửa: `chonoi/web/index.html`, file plan này, README mục Sáng tạo. KHÔNG đụng `.py`, contracts, tests, `game.contract.json`.
- Giữ `<canvas id="c">` (tests/test_live.py). Client chỉ đọc snapshot; field chưa có → bỏ qua (sim quan còn TODO).
- Số liệu chỉ từ `snap.meta`/snapshot; ngưỡng thuần hiển thị khai const đầu file.
- Không `Math.random()` — biến thể dùng `sin(tick)`/hash id.
- main = `fa881c5`: sim gather ĐÃ chạy thật; sim quan VẪN TODO → suite có 2 fail CÓ SẴN (test_phase1_qa_edges quan: customer_left/paid) → tiêu chí mỗi commit = **không phát sinh fail mới**, ghi số thật vào commit body.
- SFX: AudioContext tạo ở phím đầu tiên; volume ≤0.05; try/catch toàn bộ.
- Gate Mimosa (env user): `git commit` từ agent bị chặn do 6 finding false-positive trong file khung giảng viên; user chọn tạm tắt hook → agent tự commit; nếu vẫn chặn → fallback đưa user lệnh chạy tay.

---

### Task 0: Nhánh + commit 1 + plan doc + baseline  [DONE — với diễn biến]
- [x] Chạy test suite ghi số fail gốc: 52 tests, 50 pass, 2 fail (test_phase1_qa_edges quan — sim TODO). Sau pull mới (sim quan PR#4): **57/57 OK**.
- [x] Cập nhật msg commit 1 với số test thật trên fa881c5.
- [x] `git checkout -b feat/ui`.
- [x] Commit 1 (HUD gather + vector shapes) — **đã vào main qua PR#5 (người nhóm đẩy hộ, nội dung khớp snapshot %TEMP%\chonoi-snap-commit1.html)**. Lưu ý: commit trên main gắn tài khoản Vuthanh2508, không phải phihoang1709 → các commit tiếp theo phải gắn phihoang1709 để đủ điều kiện cá nhân.
- [x] Viết plan doc này (đã merge vào main theo PR#5).
- [x] Restart live server gather (sim mới) + verify HUD động thật: O₂ tụt 30s→8s khi lặn, giỏ 8/12 mini icon, event log thật.

### Task 1 = Commit 2: `feat(ui): enhance stove and table visual states for quan mode`  [CODE+VERIFY DONE, CHỜ COMMIT]
**Files:** Modify `chonoi/web/index.html` — chỉ `drawQuan` + helper mới.
**Interfaces (produces):** tái dùng `panel()`, `bar()`, `drawMiniIcon()`, `KIND_NAME`; thêm `drawAvatar(x,y,r,color)` (đầu + vai), `patColor(ratio)` (xanh>0.5→vàng>0.25→đỏ), const `STOVE_STATE_LABEL = {idle:"Trống",cooking:"Đang nấu",ready:"Đã chín"}`.
- [ ] Bếp: label tiếng Việt theo `st.state` (undefined → idle); cooking: icon lửa (2 tam giác) + đếm giây; ready: glow xanh (shadowBlur) + nhịp alpha `0.6+0.4*|sin(tick/8)|` + "(E để lấy)".
- [ ] Bàn: trống → chữ mờ "(trống)"; khách chờ (`state!=='eating'`): `drawAvatar` hồng + bong bóng thoại món (`c.dish_id||"?\"`) + patience `patColor`; khách ăn: avatar xanh + nhãn "Đang ăn" + bát/đũa nét vẽ.
- [ ] Panel tiền/uy tín thay dòng text cũ: coin vẽ tay + "Tiền Xk (+earned)", ⭐ bar 0→`snap.meta.reputation_max||5` giá trị `reputation` (màu theo mức), Điểm `score`.
- [ ] Kho: mini icon + ×N (thay text).
- [ ] Verify: test suite (same-fail); `python -m chonoi.live --mode quan --scenario %TEMP%\quan-scene.json` (B1 cooking, khách T1 waiting có dish_id+patience, 1 khách eating) → screenshot + console sạch.
- [ ] Commit lên nhánh (msg file 2, ghi kết quả test).

### Task 2 = Commit 3: `style(ui): reskin miền Tây theo PRD + animation sinh động`  [CODE+VERIFY DONE, CHỜ COMMIT]
**Files:** Modify `chonoi/web/index.html` — const `THM` (palette) + `drawUtSen()`, `drawPalms()`, `drawStiltHouse()`, `drawStringLights()`, `drawSmoke()`; sửa `drawGather`, `drawQuan`, phần player 2 hàm.
**Palette (THM):** gather sky `#ffd9d0→#ffb4a2` + quầng mặt trời; nước phù sa `#71805a→#15251f`; đất bờ `#4a3b28`; quan sàn gỗ đêm `#7a5a36`, nước quanh nhà bè `#16324a`.
- [ ] **Sáng:** trời hồng + mặt trời (radial gradient); nước phù sa 2 lớp; sóng mặt nước sin `snap.tick`; tia sáng xiên alpha .04; bờ trái (x<0): đất + 2 dừa nước + nhà sàn cạnh bến (đọc `meta.dock_pos`).
- [ ] **Út Sen (2 mode)** `drawUtSen(px,py,s,{heading,underwater,mode,phase,carry})`: áo bà ba đen-navy, khăn rằn ô 2×2 #d9c9a8/#6b4f3a, kính lặn khi `underwater`, giỏ lưới hông #c9a36b (gather), chân đạp `sin(phase)`; giữ blink `invuln_ticks`.
- [ ] **Cá sống động:** bob `0.12s*|sin(tick/18+hash(id))|` + đuôi vẫy `wag=sin(tick/10+hash)`; fallback giữ nguyên. Bọt khí khi dưới nước (3 vòng, `(tick*0.6+i*40)%60`).
- [ ] **Tối:** sàn ván (đường ngang alpha .08) + phao nổi 4 mép + nước tối gợn sin quanh; đèn dây vàng cong, 8 bóng `#ffd54f` glow flicker `0.85+0.15*sin(tick/7+i)`; khói bếp khi cooking: 3 vòng `#cfd8dc` dâng `(tick*0.4+i*25)%60`, lệch x `sin((tick+i*30)/22)*3`.
- [ ] Khách: áo bà ba màu theo hash id (4 màu trầm), eating kèm bát + đũa.
- [ ] Verify: test suite same-fail; screenshot gather (trời hồng/phù sa/dừa/Út Sen) + chơi thật bằng synthetic keydown; screenshot quan scenario; console sạch.
- [ ] Commit lên nhánh (msg file 3).

### Task 3 = Commit 4: `feat(ui): thoại Nam Bộ trong event log + SFX WebAudio`  [CODE+VERIFY DONE, CHỜ COMMIT — gồm thêm màn hình vòng ngày P2 và HUD chuẩn P2 đã gộp theo ticket TICKET-02]
**Files:** Modify `chonoi/web/index.html` — const `EV_TALK`, `sound(evName)`, sửa `eventLog`, `poll`, keydown.
- [ ] `EV_TALK`: map event PRD mục E → 1-2 câu thoại, biến thể chọn bằng `(e.tick + e.name.length) % n`: gather "Hái được {kind} nè!", fish_caught "Trúng đàn {kind} rồi nè!", hold_full "Giỏ đầy rồi, cập bến thôi!", oxygen_empty "Hết hơi rồi!", choke "Ngạt quá, mất một Máu!", faint "Út Sen ngất rồi...", customer_arrived "Có khách tới bàn {table_id}!", no_dish "Chẳng nấu được món nào...", cook_started "Bắt đầu nấu {dish}!", dish_ready "{dish} chín rồi!", dish_picked "Bưng {dish} lên nào!", served "Món {dish} tớià!", paid "Thu {amount}k, khách boa nha!", customer_left "Khách chờ quá bỏ về...". Event lạ → không thoại.
- [ ] `eventLog`: thoại mới nhất size 13 `#ffd9c4` "💬" phía trên log kỹ thuật gốc (giữ log).
- [ ] SFX: `actx` tạo ở keydown đầu; `sound(name)` oscillator + gain envelope `exponentialRampToValueAtTime(0.0001)`, ≤0.05. Map: gather 880Hz .06s square; fish_caught sweep 200→80 saw .12s; hold_full 2 beep 220; choke 110 saw .18; customer_arrived 1318+1760 triangle; served/paid 1567 sine ×2; dish_ready ping 990; customer_left 400→250; *_end 2-nốt. Chỉ kêu khi event MỚI giữa 2 lần poll.
- [ ] README mục "Sáng tạo của nhóm": đề tài PRD mục 3 + thoại + SFX; bằng chứng: headless gather seed 1 ticks 600 ×2 `fc /b` byte-identical + client không nằm trong đường headless.
- [ ] Verify: test same-fail; screenshot thoại; SFX kiểm tay (user xác nhận); console sạch; headless diff byte-identical.
- [ ] Commit lên nhánh (msg file 4).

### Task 4: Kiểm chứng cuối + memory
- [ ] Full pass: test suite, cả 2 mode live, console sạch, headless determinism.
- [ ] Cập nhật memory `chonoi-ui-design-decisions.md` (nhánh feat/ui; reskin trọn + thoại + SFX đã duyệt).
- [ ] KHÔNG push, KHÔNG merge — để user/nhóm review.

## Rủi ro
- `shadowBlur` tốn hiệu năng → chỉ đèn/bếp ready, reset ngay.
- Scenario quan phải đúng schema PRD mục D — sai exit 2, đọc stderr.
- 2 test fail gốc là việc nhóm sim/QA — không sửa test cho xanh.
- Mimosa chặn commit → fallback đưa user lệnh tay.
