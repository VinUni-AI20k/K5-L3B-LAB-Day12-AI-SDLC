# QUÁN ĂN CHỢ NỔI — RESEARCH UI/UX & ĐỒ HỌA GAMEPLAY KIỂU DAVE THE DIVER

> **Mục đích:** Context triển khai cho Google Antigravity; **không** phải đặc tả sửa core simulation.  
> **Dự án:** Quán Ăn Chợ Nổi — DEV 2: hái Bông Điên Điển, Bông Súng; săn Cá Linh, Cá Lóc; giỏ 12 món.  
> **Ngày rà soát nguồn:** 21/11/2026.  
> **Nguồn nghiệp vụ gốc:** file người dùng cung cấp `Pasted markdown.md` (đặc tả `chonoi/sim/gather.py`).  
> **Tham khảo thẩm mỹ:** *DAVE THE DIVER* (MINTROCKET). Chỉ học cấu trúc HUD/feedback/game-feel; KHÔNG sao chép asset, font/logo độc quyền, UI nguyên xi hoặc âm thanh.

## 0. CHỐT GIẢI PHÁP — KHÔNG CHO ANTIGRAVITY ĐOÁN

**Chọn đúng 1 Agent Skill chính:** [`threejs-game-ui-designer`](https://github.com/majidmanzarpour/threejs-game-skills/blob/main/skills/threejs-game-ui-designer/SKILL.md). Skill này có workflow HUD, menu, overlay, hierarchy, typography, responsiveness, safe-area và wiring trạng thái gameplay. **Với phần môi trường hình ảnh**, đọc thêm tài liệu phụ [`threejs-aaa-graphics-builder`](https://github.com/majidmanzarpour/threejs-game-skills/blob/main/skills/threejs-aaa-graphics-builder/SKILL.md); không cần thay skill chính.

**Chọn bộ thư viện kỹ thuật tối thiểu:**
1. **[`three`](https://www.npmjs.com/package/three)** — renderer WebGL, mô hình cá/hoa/cảnh, `Water`, `FogExp2`, `InstancedMesh`, `CSS2DRenderer` có sẵn trong hệ sinh thái chính thức.
2. **[`game-hud`](https://github.com/threejsassets/game-hud)** — thư viện giao diện HTML + CSS + JS độc lập engine, có inventory, bars, hotbar, dialogue, nhiều skin. Dùng **component/pattern**, sau đó tự đổi skin thành miền Tây sông Mekong; không lấy sẵn theme sci-fi. MIT theo README repository.
3. **[`postprocessing`](https://github.com/pmndrs/postprocessing)** — **tùy chọn**, chỉ thêm khi cần bloom/hiệu ứng màu, sau khi đã đạt FPS ổn định.

**Repository code ví dụ đúng use case:** [`wayneyip/fishtank`](https://github.com/wayneyip/fishtank) có fish schooling (boids), custom GLSL caustics và god rays — **chỉ tham khảo cách render chuyển động cá**, không import logic boids vào core gameplay Python. Repo hiện nhỏ, không nên xem là engine production hoàn chỉnh. Dự án phụ để học motion shader và instancing: [`jamisonhill/aquarium`](https://github.com/jamisonhill/aquarium), không bắt buộc cài.

**Mô hình hiển thị tối ưu:** Three.js **2.5D side-view** (mô hình 3D + màn chơi thiên về mặt phẳng 2D), camera nhìn ngang/chéo nhẹ, DOM/CSS HUD nằm trên Canvas. Lý do: contract mô phỏng dùng tọa độ `[x, d]`, `d` là độ sâu **tăng theo hướng xuống**, không có hệ tọa độ `(x,y,z)` hoặc third-person 3D tự do. Không thay đổi chiều không gian của core chỉ vì muốn đẹp.

**Luật bất di bất dịch:** `chonoi/sim/gather.py`, `game.contract.json`, kết quả `Core Simulation Runner` và contract tests phải bất biến. Antigravity chỉ xây *visual presentation layer* đọc snapshots/events.

---

## 1. UI/UX REFERENCE — HỌC DAVE THE DIVER PHẦN NÀO?

### 1.1 Reference chính thức & ảnh HUD

- **Game gốc:** https://store.steampowered.com/app/1868140/DAVE_THE_DIVER/  
  Vòng lặp gameplay quan trọng: lặn/bắt cá ban ngày → dùng nguyên liệu kinh doanh quán ban đêm. Quán Ăn Chợ Nổi giữ vòng lặp tương tự nhưng có danh tính miền Tây.
- **Ảnh HUD lặn:** https://www.pcgamer.com/dave-the-diver-review/  
  Xem cụm chỉ số nằm góc trái dưới, các control hints theo ngữ cảnh, không che nhân vật. Ảnh trực tiếp mang tính tham khảo: https://cdn.mos.cms.futurecdn.net/4MorAYBDg9E5wXcdn3kRKC-970-80.jpg
- **Ảnh dive log:** https://www.mobygames.com/game/194057/dave-the-diver/screenshots/windows/1157420/  
  Xem cách hiển thị bảng kết quả/chuyến đi, danh sách nguyên liệu theo icon/số lượng.
- **Ảnh inventory/equipment:** https://thenerdstash.com/how-to-get-white-spotted-jellyfish-in-dave-the-diver/  
  Xem ý tưởng màn hình menu, thẻ thông tin, nhưng không sao chép layout pixel-perfect.

### 1.2 Rút ra nguyên tắc (không copy)

1. **80% tầm nhìn dành cho gameplay:** màn hình luôn nhìn thấy nhân vật, cá, hoa, lối bơi và môi trường. HUD gọn thành các cụm mép màn hình.
2. **Thông tin hành động theo ngữ cảnh:** chỉ hiện `E — Hái` khi thật sự hợp lệ; chỉ hiện `SPACE — Bắt` khi ở dưới nước/có mục tiêu phù hợp và hết hồi chiêu.
3. **Cảnh báo có nguyên nhân rõ ràng:** giỏ đầy, bấm hụt, cooldown, hoa chưa mọc lại hiển thị phản hồi riêng, không dùng một thông báo chung.
4. **Số lớn và dễ đọc:** `Giỏ 8/12`, `Độ sâu 3.2m`, `Hồi chiêu 0.3s` cần đọc được ở 1920×1080 và 1366×768.
5. **Phản hồi nhanh mà không giả lập kết quả:** dùng sự kiện từ simulation cho VFX, toast và âm thanh, không phát thưởng chỉ vì animation chạm mục tiêu.
6. **Một danh tính riêng:** bảng gỗ, lưới đánh cá, màu xanh nước phù sa, vàng Bông Điên Điển, xanh lá Bông Súng, icon lồng tre; không dùng trực tiếp art/logo/font của DAVE THE DIVER.

---

## 2. ART DIRECTION: “DAVE THE DIVER — MEKONG EDITION” (CHỈ LẤY CẢM HỨNG)

- **Góc nhìn:** side-scrolling/2.5D, nhìn được toàn cảnh trên mặt nước và dưới lòng sông; có chiều sâu bằng layer parallax.
- **Bảng màu đề xuất:** xanh phù sa `#244E57`, xanh sông sâu `#102E3E`, vàng hoa `#F3CD58`, xanh lá lục bình `#70A87C`, gỗ sẫm `#674934`, kem chữ `#F6EAD2`, đỏ cảnh báo `#EC695F`.
- **Phông cảnh trên mặt:** sóng nhẹ, đám lục bình, Bông Súng, Bông Điên Điển, bến thuyền/bè gỗ, tia nắng xuyên lá, bóng phản chiếu.
- **Phông cảnh dưới mặt:** gradient nước phù sa → xanh sẫm, tia nắng xiên, hạt phù sa/bong bóng, rong/cỏ nước, thân gỗ chìm, đá, cá trôi tự nhiên.
- **Cá Linh:** hình thon bạc, bơi theo đàn; **một entity logic** có thể render thành nhiều cá *visual*. Một đợt `fish_caught` chỉ xóa đúng entity ID.
- **Cá Lóc:** thân dài, màu sẫm, bơi sâu và chậm hơn; có silhouette khác Cá Linh, tránh chỉ thay màu.
- **Cây/hoa:** Bông Súng gần mặt nước, cánh hoa sáng; Bông Điên Điển sắc vàng, dễ nhận ra từ xa. Các asset chỉ là biểu diễn trạng thái node.
- **UI vật liệu:** khung gỗ/bamboo có chiều sâu rất nhẹ, bảng số bằng mảng nền navy xanh tối, icon phẳng rõ nét; không để vân gỗ làm khó đọc.
- **Tối ưu:** giảm bloom và particles ở low quality, không bắt buộc volumetric thật; `FogExp2` là **fog theo khoảng cách**, không phải thể tích volumetric 3D đúng nghĩa.

---

## 3. WIREFRAME HUD 16:9 — MÀN ĐANG CHƠI

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ [MỤC TIÊU NGẮN]*                               [HƯỚNG DẪN]  Esc: Tạm dừng │
│                                                                             │
│  MẶT NƯỚC  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~      │
│       🌼 Bông điên điển           [E] HÁI BÔNG SÚNG                       │
│                      (Nhân vật)                                            │
│                              ↘ Bơi xuống                                  │
│                < Cá Linh F1 (đàn cá visual)   Ca Lóc F2 >                 │
│                             [SPACE] BẮT                                   │
│                [CÁ LINH +3]  ← event 'fish_caught'                          │
│                                                                             │
│  [ĐỘ SÂU] 3.2 m         [GIỎ] ■ ■ ■ ■ ■ □ □ □ □ □ □ □   5/12              │
│  [KỸ NĂNG] Bắt cá: sẵn sàng                [E] Hái | [Space] Bắt          │
└─────────────────────────────────────────────────────────────────────────────┘
```

`*` Mục tiêu nhiệm vụ, ngày/ca, đồng hồ, oxy, HP… **chỉ hiện nếu có dữ liệu authoritative từ core tương ứng**. Đặc tả DEV 2 hiện không có oxy/HP, KHÔNG tự thêm các hệ thống này.

### 3.1 Bố cục cố định

| Vùng | Nội dung | Thông tin lấy từ đâu | Hành vi |
|---|---|---|---|
| **Dưới trái** | `Độ sâu X.X m` | snapshot vị trí `[x,d]` | `d=0` mặt nước, số dương là sâu xuống; không tự đặt `d<0` |
| **Dưới giữa** | Giỏ `0..12/12`, 12 ô hoặc 12 vạch | `hold` core, thứ tự LIFO | Chỉ đọc, animate thêm từ cuối danh sách |
| **Dưới phải** | `E — Hái`, `Space — Bắt`, cooldown | state action/input + `catch_cd_ticks` | Không hiển thị action thành công khi điều kiện không đạt |
| **Trên trái** | Nhiệm vụ gần nhất (optional) | chỉ state nếu core có | Nếu thiếu data, bỏ cụm này |
| **Gần hoa/cá** | Tên, icon, prompt, viền nhấn target | authoritative node/fish snapshot | Render nhãn bằng CSS2D/DOM projection; không tính pickup ở view |
| **Giữa màn, ngắn hạn** | `+1 Bông Súng`, `+3 Cá Linh`, `GIỎ ĐÃ ĐẦY` | event + diff snapshot | 0.6–1.2 giây, chuyển động 8–16 px, không che nhân vật |

### 3.2 Màn hình/phản hồi cần có

1. **Surface Harvest State:** nhân vật nổi gần node hoa đã sẵn sàng → nhãn `E • Hái` + highlight nhẹ.
2. **Harvest Success:** event `gather` → hoa lắng/xẹp nhẹ + toast `+1` chính xác + slot cuối giỏ xuất hiện; node biến mất/tắt tương tác 20 giây.
3. **Regrowth:** event `node_regrown` → hoa bung nở mượt; prompt quay lại nếu người chơi gần.
4. **Underwater Hunt:** `d>0.5` → nút `SPACE • Bắt`, hiển thị cooldown chỉ khi chưa sẵn sàng.
5. **Catch Success:** event `fish_caught` → mục tiêu entity biến mất khỏi snapshot; hiệu ứng bọt nước + rung icon giỏ + toast số item *thực nhận*.
6. **Catch Miss:** core không emit event riêng cho hụt; UI có thể hiện hiệu ứng vung vợt khi input, nhưng không hiện `+item` hoặc xóa fish; cooldown vẫn 0.5 s.
7. **Hold Full:** event `hold_full` → giỏ rung nhẹ + viền đỏ, `GIỎ ĐÃ ĐẦY 12/12`. Cá/hoa vẫn tồn tại theo snapshot.
8. **Pause/Help:** bảng phím điều khiển ngắn gọn, áp dụng pause chỉ nếu có API pause thực tế; UI không tự pause simulation.
9. **End Dive/Inventory Summary:** danh sách item thu được, có số lượng nhóm theo loại; nếu hợp đồng yêu cầu thứ tự xuất kho thì không xáo trộn `hold` dữ liệu gốc.

---

## 4. CONTRACT GỐC — KHÔNG ĐƯỢC ĐỔI ĐỂ LÀM ĐẸP

| Trường/luật | Giá trị chính xác | Bảo toàn bởi renderer |
|---|---:|---|
| `surface_depth` | `0.5` | d ≤ 0.5: mặt nước; d > 0.5: vùng săn cá |
| `interact_radius` | `2.0` | render chỉ gợi ý, core quyết định kết quả |
| `node_yield` | `1` | thành công thêm 1 item |
| `regrow_s` | `20.0` s | 1200 ticks @60 Hz, event `node_regrown` |
| `catch_radius` | `2.0` | render không tự lựa mục tiêu khác core |
| `catch_cooldown_s` | `0.5` s | 30 ticks @60 Hz; input spam không bypass |
| `fish_yield.ca_linh` | `3` | có thể bị cắt bớt do giỏ gần đầy |
| `fish_yield.ca_loc` | `1` | chỉ tăng item khi core xác nhận |
| `hold_capacity` | `12` | 12 ô, KHÔNG tạo inventory mới |
| `hold` | danh sách LIFO | append cuối, giữ thứ tự logic |
| `node` | `{id,kind,pos:[x,d],regrow_ticks}` | render theo ID và regrow state |
| `fish` | `{id,kind,pos:[x,d],heading_deg}` | render theo ID; không tự sinh entity logic |

**Lưu ý rất dễ sai:** Với giỏ 11/12, bắt Cá Linh logic thu 3 nhưng `hold` chỉ tăng 1, và fish entity bị xóa. Toast phải báo `+1 Cá Linh` chứ không báo `+3`. Dùng `next.hold.length - prev.hold.length` hoặc diff authoritative, không chỉ nhìn `kind` để đoán số lượng.

**Tie-breaking:** Khi có nhiều target gần tương đương, core mới chọn ID theo sort/tie-breaker; view có thể highlight target từ dữ liệu authoritative nếu có, không tự chọn mục tiêu để gửi vào core làm thay đổi luật.

**Tọa độ:** Core `[x,d]` là mặt phẳng logic 2D. Adapter đề xuất ánh xạ `Vector3(x, seaLevelY - d, 0)`; chiều sâu parallax của cá nền là biến visual riêng `zVisual` và **không làm đổi khoảng cách tương tác core**.

**Events đã có:** `gather`, `node_regrown`, `fish_caught`, `hold_full` (và các event khác nếu codebase có). Mỗi event trigger tối đa một chuỗi feedback của view; nếu snapshot replay cần dedupe theo tick/index/event ID do adapter bổ sung mà không sửa core.

---

## 5. THƯ VIỆN & MÃ MẪU — LINK ĐÃ ĐỐI CHIẾU

### A. Skill chính: `threejs-game-ui-designer`

- Skill: https://github.com/majidmanzarpour/threejs-game-skills/blob/main/skills/threejs-game-ui-designer/SKILL.md
- Hướng dẫn UI patterns: https://github.com/majidmanzarpour/threejs-game-skills/tree/main/skills/threejs-game-ui-designer/references
- Dùng cho HUD zones, menu, typography, safe areas, mobile và UI-state wiring.
- Cài bằng skills CLI nếu cấu hình đúng agent: `npx skills add majidmanzarpour/threejs-game-skills --skill threejs-game-ui-designer`.
- Không để agent dùng template scaffold tạo lại project đang có.

### B. HTML HUD: `game-hud` (ưu tiên)

- GitHub: https://github.com/threejsassets/game-hud
- Live demo: https://threejsassets.github.io/game-hud/
- NPM: https://www.npmjs.com/package/game-hud
- Cài: `npm install game-hud`
- Có CSS core, skin, inventory/hotbar/dialogue. Dùng HTML overlay + CSS, bắt đầu với `nature`/`pixel` và custom CSS Mekong. Không bật các thanh HP, mana, ammo nếu gameplay không có.
- Repo README ghi MIT; kiểm tra thêm LICENSE của release cài thực tế.

### C. Render gameplay: Three.js official

- Three.js: https://threejs.org/
- `Water`: https://threejs.org/docs/pages/Water.html (add-on reflection trên **WebGLRenderer**; reflection texture càng lớn càng tốn GPU).
- `FogExp2`: https://threejs.org/docs/pages/FogExp2.html (fog theo khoảng cách, không phải true volumetric fog).
- `InstancedMesh`: https://threejs.org/docs/pages/InstancedMesh.html (nhiều instance cùng geometry/material → giảm draw calls).
- `CSS2DRenderer`: https://threejs.org/docs/pages/CSS2DRenderer.html (nhãn theo world point; HUD cố định nên dùng DOM riêng).
- Three.js examples: https://threejs.org/examples/

### D. Cá bơi, mặt nước, tia nắng

- Fish schooling + caustics sample: https://github.com/wayneyip/fishtank (MIT; dùng để nghiên cứu demo, KHÔNG để boids thay core fish positions).
- Fish shader/instancing sample: https://github.com/jamisonhill/aquarium (tham khảo các file `FishFactory.ts`, `shaders.ts`, `Environment.ts`; đọc LICENSE trước khi copy code).
- `pmndrs/postprocessing`: https://github.com/pmndrs/postprocessing (bloom tùy chọn, chỉ dùng sau profiling).
- `threejs-aaa-graphics-builder` reference kỹ thuật đồ họa: https://github.com/majidmanzarpour/threejs-game-skills/blob/main/skills/threejs-aaa-graphics-builder/SKILL.md

### E. Tài liệu Antigravity chính thức

- Skill locations: https://antigravity.google/docs/skills
- Workspace skill đặt tại `<repo>/.agents/skills/mekong-dive-ui/SKILL.md` (không phải mặc định `.agent/skills`, dù một số phiên bản có backward compatibility).
- Global skills: `~/.gemini/config/skills/<skill-folder>/SKILL.md`.
- Skill có YAML frontmatter `name` / `description`; kiểm tra Antigravity đã nhận skill rồi mới chạy task.

---

## 6. KỸ THUẬT RENDER GAMEPLAY (KHÔNG LÀM MẤT 60 FPS)

### 6.1 Scene 2.5D

```text
                          ┌───────────────────────────────┐
 Python Headless Core      │ snapshot & events            │
 chonoi/sim/gather.py ────>│ Python→JSON/WebSocket/adapter│ (theo transport hiện hữu)
                          └──────────────┬────────────────┘
                                         ▼
                               Presentation State (TS)
                                 /               \
                                ▼                 ▼
                      Three.js World           DOM/CSS HUD
                      (fish, water, flora)     (12 slot, hints)
                         read-only               read-only
```

- Core vẫn chạy không cần GUI (`pytest`, CLI). Không import Three.js vào package Python.
- Bridge UI sử dụng snapshot/events **mà hệ thống đã có**; nếu thiếu cần viết một adapter bên ngoài core, không tự thay đổi cấu trúc trả về hoặc event contract.
- Đồng hồ render `requestAnimationFrame` khác 60-tick simulation. Nội suy transforms bằng frame delta để mượt, logic giữ nguyên tick fixed.
- Cờ hiệu visual không làm thay đổi target selection, positions hoặc trạng thái hold trong core.

### 6.2 Render nước & không khí

- **Đầu tiên:** plane nước màu xanh có normal/map nhẹ, ripple nhỏ, gradient màu theo độ sâu, ánh sáng xiên và bubbles.
- **Sau đó:** dùng `Water` reflection theo WebGL nếu phù hợp, quality tier trung/cao. Với gameplay 2.5D, visual có thể đẹp hơn và tiết kiệm hơn nếu dùng shader 2D/transparent plane đơn giản.
- Dùng `FogExp2` + tint cảnh dưới nước; không cần true volumetric tốn kém. Render caustic giả qua texture scrolling, 1–2 rays dạng mesh translucent.
- Tạo flora/rock từ module low-poly; có thể dùng `InstancedMesh` riêng cho từng nhóm geometry/material; **không hứa tất cả props chỉ mất 1–2 draw calls**.

### 6.3 Fish render & synchronization

- `FishVisualFactory(kind)` tạo 1 mô hình hình học/asset cá đúng loài.
- Cá Linh `F1` có thể spawn 3–8 cá *trang trí theo đàn* rải quanh anchor `F1` (dùng deterministic visual hash từ `F1` để không nhảy mỗi frame). `F1` vẫn là 1 entity; chỉ F1 được core bắt.
- Cá Lóc hiển thị đơn độc, đuôi đánh nhịp chậm. Animation body undulation ở vertex shader nếu có thể, nhưng x/d anchor lấy từ snapshot.
- Khi F1 biến mất khỏi `next.fish`, tạo catch VFX rồi despawn cả đàn visual đúng ID. Không tăng số lượng cá tương tác tùy ý.
- Instancing có lợi khi cùng mesh/material; fish vật lý với rig riêng có thể cần shader/morph animation hoặc mesh riêng tùy mức độ chi tiết.

### 6.4 UI update không spam re-render

- UI là HTML overlay dùng state snapshot, render-on-change từ tick/bridge, không React setState mỗi `requestAnimationFrame` nếu không cần.
- Cooldown UI có thể nội suy hiển thị `catch_cd_ticks / 60`, nhưng **không bao giờ ra quyết định có được bắt** dựa trên đồng hồ UI.
- Responsive safe-area: 1920×1080, 1366×768, 390×844; dùng `clamp()` cho chữ và cỡ nút.
- Sử dụng DOM semantics: focus, keyboard hint, contrast, tắt flashing quá mạnh. Nút di động chỉ khi game target mobile.

---

## 7. HỢP ĐỒNG PHẢN HỒI UI — SOURCE OF TRUTH

| Trigger | UI/VFX | Không được làm |
|---|---|---|
| User nhấn `E`, core emit `gather` | Hoa lóe nhẹ, `+1`, giỏ tăng | Hiện thành công chỉ vì phím được nhấn |
| `node_regrown` | Hoa trở lại, có glow nhỏ | Regrow dựa vào đồng hồ JS thay vì 1200 tick |
| User nhấn `Space`, không `fish_caught` | Animation vung vợt hụt + cooldown chỉ nếu core báo cooldown state | Tự xóa fish / tự thêm đồ |
| `fish_caught` | VFX nước, cá biến mất theo snapshot, toast số thực nhận | Luôn thông báo `+3` với Cá Linh khi giỏ chỉ còn 1 ô |
| `hold_full` | Viền giỏ đỏ, tooltip `Giỏ đầy 12/12` | Despawn fish/node hay tràn > 12 |
| Player ở dock | Ẩn `E Hái` | Cho hái tại dock |
| `d=0.5` | Surface interaction | Cho phép `Space` bắt cá |
| `d=0.5001` | Underwater interaction | Cho phép `E` hái hoa |

---

## 8. TỔ CHỨC FILE ĐỀ XUẤT (CHỈ PHẦN UI/RENDER)

```text
<repo>/
├── chonoi/sim/gather.py            # KHÓA / NO EDIT
├── game.contract.json             # KHÓA / NO EDIT
├── tests/                         # giữ tests gốc
├── web/                           # chỉ nếu repo đã có hoặc phù hợp cấu trúc hiện tại
│   └── src/
│       ├── bridge/
│       │   ├── SnapshotAdapter.ts
│       │   └── EventVisualMapper.ts
│       ├── scene/
│       │   ├── MekongWorld.ts
│       │   ├── WaterSurface.ts
│       │   ├── FishVisuals.ts
│       │   ├── HarvestNodesVisuals.ts
│       │   └── MekongAtmosphere.ts
│       ├── ui/
│       │   ├── GameplayHUD.ts
│       │   ├── Basket12Slots.ts
│       │   ├── InteractionPrompt.ts
│       │   ├── CatchFeedback.ts
│       │   └── theme-mekong.css
│       └── main.ts
└── .agents/
    └── skills/
        └── mekong-dive-ui/
            └── SKILL.md
```

**Không tự tạo `web/` nếu hiện tại repo đã có frontend khác.** Đọc file trước, dùng cấu trúc thực tế, chỉ tách package khi cần và không ảnh hưởng chạy headless.

---

## 9. TIÊU CHUẨN HOÀN THÀNH (ACCEPTANCE CRITERIA)

### Hình ảnh/UX

- [ ] Có cảnh sống động sông Mekong: đường mặt nước, bến/bè, hoa nổi, rong, đá, đàn Cá Linh, Cá Lóc.
- [ ] HUD gọn: Depth, Hold 0–12, Catch cooldown, E/Space hints đúng bối cảnh.
- [ ] Màn lặn và mặt nước chuyển màu/ánh sáng mượt, nhưng không che đường chơi.
- [ ] Ít nhất 7 state VFX đúng phần 3.2, có ảnh/video kiểm chứng.
- [ ] Có palette miền Tây riêng; không copy art DAVE THE DIVER.
- [ ] Screenshot 1920×1080 và 1366×768 không cắt/chồng HUD.

### Logic/headless

- [ ] `chonoi/sim/gather.py` chưa bị sửa.
- [ ] `game.contract.json` chưa bị sửa.
- [ ] Full test contract chạy nguyên vẹn trong CLI headless.
- [ ] Check 10 edge cases EC-01..EC-10: dock, 0.5001, 0.5, 11/12, 12/12, tie-break, cooldown 30 ticks, node regrow 1200 ticks, empty fish, LIFO export.
- [ ] Snapshot→visual mapping dùng ID ổn định; không có fish/flower logical giả.
- [ ] Renderer stop/restart không làm đổi simulation state.

### Performance/quality

- [ ] Mục tiêu 60 FPS ở thiết bị mục tiêu, ghi rõ GPU/trình duyệt/cửa sổ test; không tuyên bố đạt nếu chưa đo.
- [ ] Chụp benchmark `renderer.info.render.calls`, triangles, renderer time, memory.
- [ ] Có quality tiers giảm pixel ratio, particles, caustics, shadow, reflection.
- [ ] Không còn errors/warnings quan trọng trong browser console.
- [ ] Danh sách file đã sửa, screenshots trước/sau, command chạy test, kết quả thật.

---

## 10. PROMPT DÁN THẲNG VÀO GOOGLE ANTIGRAVITY

```text
ROLE: Senior Three.js WebGL Game UI/UX Engineer and Technical Artist.

PROJECT: Quán Ăn Chợ Nổi — DEV 2 Mekong Gathering & Fishing Gameplay.
VISUAL REFERENCE: DAVE THE DIVER for readable HUD, underwater feel and instant feedback ONLY; create original Mekong-themed UI and artwork.

FIRST ACTIONS:
1. Read the attached Quán Ăn Chợ Nổi UI/UX research .md and the provided DEV 2 gameplay specification in full.
2. Inspect the actual repository: frontend, rendering entrypoint, snapshot transport, Python simulation runner, test commands, game.contract.json.
3. Read the threejs-game-ui-designer SKILL.md and its UI reference before modifying screens.
4. Produce a short audit with exact files you intend to modify. DO NOT scaffold a replacement project.

IMPLEMENT:
A. One screen of live playable 2.5D Mekong river gameplay using the current Three.js renderer (or integrate Three.js into the current frontend only if necessary).
B. Visual player, flowers, cá linh school, solitary cá lóc, waterline, riverbank vegetation, depth water color, fog particles, caustics/light shafts (with quality toggles).
C. High-quality compact HUD: depth; hold as 12 slots and x/12; catch cooldown; contextual E-harvest and Space-catch prompts; event-based +item and hold-full alerts; pause/help only when supported.
D. Event-driven animations using real simulation snapshots and events, not invented frontend gameplay rules.
E. Original Vietnam Mekong art direction, not reused Dave the Diver textures/logo/sounds.

MANDATORY CONTRACT:
- NEVER change chonoi/sim/gather.py, game.contract.json, test semantics or fixed 60 Hz simulation tick.
- 2D sim position [x,d] where d increases downward: visual map (x, seaLevelY - d, visualZ). visualZ does not affect sim interaction distances.
- surface_depth=0.5; interact_radius=2; catch_radius=2; regrow=1200 ticks; cooldown=30 ticks; hold_capacity=12.
- Fish F1 is ONE logical entity even if drawn as many schooling meshes.
- Catch yield ca_linh=3 or ca_loc=1 is capped by available hold capacity. Display actual snapshot delta (e.g., with 11/12, show +1 ca_linh, not +3).
- Do not add O2, HP, weight, weapons, or new interactions unless the existing authoritative core supplies them.
- No core changes or DOM/WebGL imports into headless simulation.

DELIVERABLES:
1. An integrated playable HUD + visually improved actual gameplay scene, not a static concept picture or dashboard.
2. Changed files and concise rationale.
3. Screenshot at 1920x1080, 1366x768; optional 390x844 only if mobile support exists.
4. Demonstration of gather success, regrowth, catch success, catch miss, hold full, 11/12 ca linh catch, exact depth 0.5 and 0.5001 transitions.
5. Actual CLI headless tests and browser checks; report whether every test passed. Do not claim unrun tests.
6. FPS/draw calls/frame time in a stated test environment; optimize low-tier fallbacks when necessary.

Start with the HUD + one representative fishing scene. Do not change unrelated systems or claim completion until the acceptance checklist passes.
```

---

## 11. THỨ TỰ LÀM — CHỈ GIAI ĐOẠN GIAO DIỆN GAMEPLAY DEV 2

1. **Ngày 1:** Audit repo, xác định snapshot transport, dựng HUD cho state giả lập *read-only* để review bố cục; không sửa core.
2. **Ngày 2:** Nối state thật: depth, `hold`, cooldown và action prompts; test d=0.5 / d=0.5001 và giỏ 11/12.
3. **Ngày 3:** Dựng 1 cảnh sông Mekong có Cá Linh, Cá Lóc, Bông Súng, Bông Điên Điển và UI nhãn.
4. **Ngày 4:** Kết nối event `gather`, `node_regrown`, `fish_caught`, `hold_full`; thêm VFX, cường độ phù hợp.
5. **Ngày 5:** Thêm reflection/fog/caustics, benchmark, capture screenshots, chạy toàn bộ headless contract + edge cases.

> Đây là kế hoạch gợi ý, không phải cam kết thời gian triển khai. Đạt acceptance mới chuyển bước tiếp.

## 12. BẢNG NGUỒN THAM KHẢO ĐÃ ĐỐI CHIẾU

| Nguồn | Sử dụng | Link |
|---|---|---|
| DAVE THE DIVER trên Steam | Loop gameplay và tham khảo thương mại chính thức | https://store.steampowered.com/app/1868140/DAVE_THE_DIVER/ |
| PC Gamer gameplay review | Ảnh UI lặn | https://www.pcgamer.com/dave-the-diver-review/ |
| MobyGames Dave dive log | UI màn kết quả | https://www.mobygames.com/game/194057/dave-the-diver/screenshots/windows/1157420/ |
| Three.js Game UI Designer | Skill chính | https://github.com/majidmanzarpour/threejs-game-skills/blob/main/skills/threejs-game-ui-designer/SKILL.md |
| Three.js AAA Graphics Builder | Reference đồ họa phụ | https://github.com/majidmanzarpour/threejs-game-skills/blob/main/skills/threejs-aaa-graphics-builder/SKILL.md |
| game-hud | HTML+CSS inventory/HUD kit | https://github.com/threejsassets/game-hud |
| Three.js Water | Water effect WebGL | https://threejs.org/docs/pages/Water.html |
| Three.js FogExp2 | Fog theo khoảng cách | https://threejs.org/docs/pages/FogExp2.html |
| Three.js InstancedMesh | Batching cá/props | https://threejs.org/docs/pages/InstancedMesh.html |
| Three.js CSS2DRenderer | World labels | https://threejs.org/docs/pages/CSS2DRenderer.html |
| wayneyip/fishtank | Fish schooling + caustics code | https://github.com/wayneyip/fishtank |
| jamisonhill/aquarium | Fish shader & water motion reference | https://github.com/jamisonhill/aquarium |
| pmndrs/postprocessing | Bloom/fx tùy chọn | https://github.com/pmndrs/postprocessing |
| Google Antigravity Agent Skills | Thư mục workspace skill chuẩn | https://antigravity.google/docs/skills |

**Giới hạn kiểm chứng:** Các nguồn công khai xác minh khả năng kỹ thuật của package/demo. Chưa đo benchmark trên chính codebase Quán Ăn Chợ Nổi. Một repo demo cá bơi không thay thế được thuật toán, state và bài test của hệ mô phỏng hiện tại.
