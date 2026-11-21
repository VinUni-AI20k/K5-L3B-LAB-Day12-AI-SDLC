# PRD-0 — Quán Ăn Chợ Nổi (Phase 1): bản ghi của nhóm

> **Nguồn gốc:** tab Phase 1 của [Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg#phase-1) (phát hành 08:02, hạn tag `phase-1` lúc **1:00** giờ lab).
> Đây là bản **chép lại có tóm gọn** để agent và cả nhóm đọc trong repo. Khi có chỗ lệch thì **lab board là chuẩn**; thấy lệch thì sửa file này và ghi vào `docs/clarify.md`.
> Code trong `chonoi/` có nhắc "PRD mục 13.2" và "mục 13.8". Hai mục đó ứng với **mục A (dải hợp lệ)** và **mục F (luật một bước)** ở dưới.

Day 12 · AI SDLC · nhóm 4–6 người · 60 phút (0:00–1:00) · **Test Contract v1.0**

---

## 1. Chúng tôi muốn gì

Game quản lý quán ăn mang bản sắc miền Tây Nam Bộ. Nhân vật chính là Út Sen, cô bé ở chợ nổi Rạch Sen, phụ Má Tư đang đau lưng:
- **Buổi sáng:** lặn bắt cá, hái rau trên sông Chín Khúc.
- **Buổi tối:** nấu ăn và phục vụ khách trên nhà bè.

Những gì mang về buổi sáng quyết định buổi tối bán được món nào.

**Tự do sáng tạo:** nhóm được thêm nhân vật, loài cá/cây, sinh vật, món, khu vực, cơ chế nhỏ, sự kiện, câu chuyện, đồ họa, âm nhạc, giao diện, với ba điều kiện:
1. Giữ đúng luật lõi, số chuẩn và Test Contract. Phần tự thêm phải **tắt ở headless**, hoặc bảo đảm không đổi tick, sự kiện, tiền, uy tín và snapshot theo contract khi chạy test.
2. Ghi ý tưởng vào mục **"Sáng tạo của nhóm"** trong `README.md`, kèm bằng chứng ngắn cho thấy lõi vẫn đúng.
3. Làm lõi đúng trước, sáng tạo sau. Điểm sáng tạo thuộc hạng mục chất lượng sản phẩm; độ phức tạp không được cộng điểm.

## 2. Phạm vi Phase 1

**Lõi (mọi nhóm):**
- **Buổi sáng (`gather`):** bơi trong mặt cắt 2D của sông, tọa độ `[x, d]` (x theo chiều ngang, d là độ sâu).
  - Út Sen tiêu oxy khi dưới nước, hồi oxy khi nổi lên, có **3 Máu** và chỉ mất Máu do ngạt.
  - Hái tại nút trên mặt nước; dùng nút bắt (`catch`) khi đang lặn. Bản mặc định có **6 đàn cá đứng yên**.
  - Giỏ có sức chứa giới hạn. Cập bến hoặc hết giờ thì bàn giao phần còn trong giỏ qua file kho. Ngất thì kết thúc buổi sáng với kho rỗng.
- **Buổi tối (`quan`):** quán có **1 bếp B1, 1 bàn T1 và 3 món**.
  - Khách chọn món nấu được với kho khả dụng và giữ chỗ nguyên liệu khi gọi.
  - Người chơi nấu → bưng → phục vụ trước khi khách hết kiên nhẫn.
  - Khách ăn xong trả tiền, có thể boa. Khách hết kiên nhẫn làm giảm uy tín.
- **Nối hai buổi:** hai buổi chơi riêng và nối nhau qua **hai tiến trình headless dùng chung file kho**.
- **Điều khiển gợi ý:** WASD/mũi tên để bơi/đi, **E** để tương tác, **Space** để bắt cá.
- **HUD tối thiểu:**
  - buổi sáng: thời gian, oxy, Máu, giỏ;
  - buổi tối: kho khả dụng, món gọi, kiên nhẫn, trạng thái bếp, món trên tay, tiền, uy tín.

**Mở rộng:** kỳ vọng tính cho cả buổi lab. Nhóm 4 người không bắt buộc, nhóm 5 người hoàn thành ít nhất 1 mục, nhóm 6 người ít nhất 2 mục. Danh sách mục mở rộng chưa có trong PRD-0.

## 3. Cảm giác và phong cách

- **Khung cảnh:** sông nước màu phù sa, bờ dừa nước, nhà sàn, ánh hồng buổi sớm; tối có đèn dây vàng và khói bếp.
- **Nhân vật:** Út Sen mặc áo bà ba, buộc khăn rằn, đeo kính lặn tự chế và giỏ lưới.
- **Góc nhìn:** mặt cắt nhìn ngang cho cảnh lặn, nhìn từ trên xuống cho nhà bè. Có thể bắt đầu bằng hình khối 2D.
- **Lời thoại:** khuyến khích giọng Nam Bộ.
- **Văn hóa và tài sản:** tôn trọng văn hóa địa phương; chỉ dùng tài sản có quyền sử dụng và ghi nguồn trong `CREDITS.md`.

## 4. Công nghệ và cách vào lab

**Công nghệ:** starter Python chỉ là một lựa chọn; nhóm được chọn ngôn ngữ, engine, thư viện. Nếu đổi công nghệ thì cập nhật `build_cmd`, `run_cmd`, `headless_cmd` để giữ đúng Test Contract. Smoke test chạy **hộp đen qua `headless_cmd`**.

**Vào lab:**
1. Trưởng nhóm fork repo lớp, đặt tên `K5-L3B-LAB-Day12-AI-SDLC-<ten-nhom>`.
2. Mời các thành viên làm collaborator với quyền Write. Để repo public là đủ cho giảng viên xem.
3. Điền `TEAM.md` và đặt `team_size` trong `game.contract.json` khớp số thành viên thực tế.

Nhóm có thể bật GitHub Actions hoặc ruleset nếu hợp với cách làm đã chọn.

## 5. Nguyên liệu và món

| ID nguyên liệu | Tên |
|---|---|
| `ca_loc` | Cá lóc |
| `ca_linh` | Cá linh |
| `bong_dien_dien` | Bông điên điển |
| `bong_sung` | Bông súng |

| ID món | Món | Công thức |
|---|---|---|
| `ca_loc_nuong_trui` | Cá lóc nướng trui | `ca_loc` ×1 |
| `goi_bong_sung` | Gỏi bông súng | `bong_sung` ×2 |
| `lau_ca_linh_dien_dien` | Lẩu cá linh bông điên điển | `ca_linh` ×3 + `bong_dien_dien` ×1 |

Dùng preset mẫu, hoặc tự chọn giá, thời gian nấu và các số khác trong dải cho phép ở mục A. Phải khai đúng giá trị đang chạy trong `tuning`.

## 6. Cách làm việc nhóm

**Quy trình kỹ thuật do nhóm tự chọn:** push thẳng, nhánh + PR, pair/mob hoặc review trực tiếp đều được.
- Cả nhóm chia việc, phối hợp và tích hợp các module trong **một fork chung**.
- Mỗi người commit bằng tài khoản GitHub của mình, **tối thiểu 3 commit có nội dung** trong cả buổi lab. Commit của người không có trong `TEAM.md` không được tính.
- Làm chung một commit thì ghi `Co-authored-by:` cho người cùng làm.

**Nên dùng (tùy chọn, không làm cũng không bị trừ điểm):** CI/CD, PR có review và approval, bảo vệ nhánh, ruleset, issue/board, CODEOWNERS, ADR hoặc template. Ví dụ: ghi hợp đồng ở `docs/contracts/` và nhờ hai người duyệt PR đổi schema. Thực hành hiệu quả được cộng ở hạng mục thực hành kỹ thuật.

### 6.1. Kickoff và planning trong 15 phút đầu
1. **Chia vai:** chia bốn lát (mục 6.2) và ghi vào `TEAM.md` tên, GitHub handle, module chính, vai của từng người (có thể kiêm vai).
   - **PO** hỏi **Anh Năm hàng xóm** (trợ giảng AI ở tab Phase 1 của lab board; anh đóng vai khách hàng, trả lời ngắn các chỗ PRD chưa nói rõ) hoặc hỏi giảng viên.
   - **Integrator** điều phối tích hợp và gắn tag.
   - **QA lead** giữ bộ test và ma trận truy vết.
   - **Scrum/Release** theo dõi mốc bàn giao.
2. **Thỏa thuận nhóm:** chốt ngắn trong `TEAM.md` gồm kênh liên lạc, giờ standup, cách quyết khi bất đồng, việc cần làm khi có người trễ hoặc vướng. Ví dụ: trao đổi 2 phút rồi nhờ người đã thống nhất chốt; báo kênh nhóm khi vướng quá 10 phút.
3. **Hợp đồng file kho:** chốt sớm hợp đồng giữa `gather` và `quan` theo mục G.
   - Ghi schema và một ví dụ kho hợp lệ trong `README.md` hoặc `docs/contracts/`.
   - Chốt các sự kiện và giao diện giữa mô phỏng và UI (`sim/*` ↔ `client/ui`: trạng thái đọc được, lệnh gửi vào).
   - Sau khi thống nhất thì bắt đầu các lát song song; lát quán dùng kho mẫu để làm.
4. **Backlog (nếu cần):** dùng checklist, issue/board hoặc `docs/plan/phase-1.md`. Gợi ý ghi đầu việc, mã `AC-P1-xx`, người làm và phụ thuộc.

### 6.2. Bốn lát làm song song

| Lát | Phạm vi |
|---|---|
| 1 | Bơi, oxy, chặn biên, giỏ |
| 2 | Hái, bắt cá, cập bến, ghi file kho |
| 3 | Khách, giữ chỗ nguyên liệu, kiên nhẫn |
| 4 | Bếp, bưng, phục vụ, tiền |

- **Chia người:** nhóm 4 người có thể giao mỗi người một lát. Người thêm ở nhóm 5–6 có thể lo HUD, QA hoặc hỗ trợ lát chậm.
- **Phối hợp:** gợi ý review chéo giữa các lát, đổi vai người lái/người dẫn đường khi pair/mob.
- **Phút 20 của mỗi phase:** rà lát đang vướng, điều người đã xong sang hỗ trợ.
- **Standup:** gói trong 2–3 phút, ba ý: đã xong, sắp làm, đang vướng.

### 6.3. Kiểm chứng và ghi chép
- **Kiểm chứng mỗi phase:** chạy trên commit bàn giao ở `main` và đẩy tag `phase-n` đúng hạn.
  - Ghi `docs/verification/phase-n.md` theo dạng **AC → bằng chứng → kết quả đạt/chưa đạt**, kèm cách kiểm chứng.
  - Ở Phase 1, lưu kết quả thật trong `docs/proof/phase-1/` và dẫn link từ `docs/verification/phase-1.md`.
- **Chỗ PRD mơ hồ:** hỏi Anh Năm trước; anh không trả lời được thì nhóm tự đặt giả định. Ghi câu hỏi, trả lời và quyết định vào `docs/clarify.md`.
- **Ghi chép khác:**
  - `docs/ai-usage-log.md` theo người và phase, kèm token/chi phí nếu đo được;
  - retro trong `docs/retro.md`;
  - phản tư mỗi người trong `docs/members/<handle>.md`.
- **Đánh giá cá nhân:** dựa trên **bằng chứng trong repo chung** (commit từng người, phần mình làm, việc giúp người khác), phản tư cá nhân và đánh giá chéo. Số PR và lượt review không dùng để chấm cá nhân.

### 6.4. Lịch gợi ý (60 phút)

| Phút | Việc |
|---|---|
| 0–15 | Vào fork, chia vai, ghi `TEAM.md`, chốt hợp đồng kho, bắt đầu các lát song song |
| 15–45 | Build và phối hợp các lát. Rà hỗ trợ ở **phút 20**, **thử xuất file kho thật trước phút 25**, standup giữa phase |
| 45–55 | Chạy smoke hai tiến trình và chơi thử trên `main`. Hoàn thiện ma trận truy vết và gắn tag |
| 55–60 | Dự phòng. Đẩy `phase-1` chậm nhất **1:00** |

## 7. Định nghĩa hoàn thành (DoD)

- [ ] Chơi được cả hai buổi, đúng phạm vi lõi. HUD đọc được trong lúc chơi.
- [ ] `game.contract.json` khớp bản chạy và đủ Test Contract v1.0. Smoke hai tiến trình trên `main` cho thấy quán nhận đúng file kho.
- [ ] `README.md` ghi cách chạy từ clone sạch trong **tối đa 3 lệnh** trên macOS hoặc Linux, cách điều khiển, cách tính điểm và lệnh test. Test của nhóm chạy được bằng **1 lệnh**.
- [ ] Fork chung có đủ collaborator; commit gắn với tài khoản GitHub của từng người. `TEAM.md` có danh sách và thỏa thuận nhóm; `team_size` khớp danh sách.
- [ ] Hợp đồng kho đã thống nhất, có schema và ví dụ hợp lệ trong `README.md` hoặc `docs/contracts/`.
- [ ] Có `docs/verification/phase-1.md` và bằng chứng chạy ở commit gắn tag. Đã cập nhật ghi chép tối thiểu ở mục 6.3.
- [ ] Nếu có phần tự sáng tạo: mục "Sáng tạo của nhóm" trong `README.md` có bằng chứng lõi vẫn đúng.
- [ ] Tag `phase-1` trỏ tới commit bàn giao trên `main`, chậm nhất **1:00**.

---

# Test Contract v1.0 (bắt buộc)

Headless chạy logic ở **60 tick/s**, độc lập với cửa sổ, GPU và tốc độ render. Đơn vị vị trí là mét.
- `gather` dùng `[x, d]`: x hướng đông, d tăng xuống dưới; hướng 0° là +x, 90° là xuống.
- `quan` dùng `[x, z]`: z hướng bắc.

## A. File `game.contract.json` ở gốc repo

**Các khóa bắt buộc:** mọi khóa trong preset v1.0 đều bắt buộc. Có thể dùng nguyên bộ số mẫu; repo này đang dùng đúng preset.
- `team` là mã nhóm, `team_size` là số thành viên thực tế.
- `headless_cmd` nhận các cờ ở mục B; `run_cmd` mở game; `build_cmd` chuẩn bị bản chạy.

**Quy đổi:** thời gian có hậu tố `_s` quy ra số tick nguyên ở 60 Hz. Tiền lưu bằng số nguyên, đơn vị nghìn đồng.

**Dải hợp lệ:**

| Tham số | Dải |
|---|---|
| Thời lượng hai ca | 60–600 s |
| Khoang (giỏ) | 4–30 ô |
| Kiên nhẫn | 20–180 s |
| Bán kính bến/hái/bắt/tương tác quán | 0.5–5 m |
| Tốc độ bơi/đi | 1–10 m/s |
| Hồi bắt | 0–10 s |
| Oxy tối đa | 10–120 s |
| `ramp_max_ticks` | 0–6 tick |

- **Số dương:** giá là số nguyên dương; thời gian nấu, mọc lại, ăn và chu kỳ khách là số tick dương sau quy đổi.
- `first_customer_tick` nguyên dương và trước khi đóng ca.
- `tip_rate > 0`, `tip_min_patience_ratio ∈ (0, 1]`, `tip_reputation > 0`, `left_reputation_delta < 0`.
- Thời lượng, khoang, oxy, kiên nhẫn đều hữu hạn.
- **Các luật và giá trị còn lại lấy theo preset.** Riêng vị trí các nút và đàn cá được chọn trong miền hợp lệ.
- **Cố định:** ID và công thức 3 món; 4 loại nguyên liệu, mỗi nguyên liệu chiếm 1 ô; 1 bếp B1, 1 bàn T1; ít nhất một nút mỗi loại cây; 6 đàn cá đứng yên có cả hai loài; `burn_s: null`.
- **Vị trí:** nút mặc định đặt ở `d = 0`; đàn cá ở dưới nước.

## B. Tham số headless

```
<headless_cmd> --mode gather|quan --seed <int>
  [--scenario <file.json>] [--inputs <file.json>] [--inventory <file.json>] [--inventory-out <file.json>]
  --ticks <N> --out <file.jsonl> [--snapshot-every <K>]
```

- **Cờ bắt buộc:** `--mode`, `--seed`, `--ticks`, `--out`.
  - Seed là số nguyên có dấu, biểu diễn chính xác trong JSON.
  - `--ticks` là số bước ngoài tối đa, nguyên không âm; giá trị 0 chỉ dựng fixture.
  - `--snapshot-every` là số nguyên dương, mặc định 10.
- **Cờ kho:** `--inventory` chỉ dùng với `quan`, `--inventory-out` chỉ dùng với `gather`. Đầu ra dùng đường dẫn riêng, tách khỏi đầu vào.
- **Mã thoát:**
  - **0:** kết thúc lượt hoặc chạm giới hạn bước;
  - **2:** cờ/dữ liệu sai hoặc fixture mâu thuẫn;
  - **1:** lỗi thực thi hoặc lỗi ghi đầu ra.

  Chẩn đoán in ra stderr. Lỗi dữ liệu phải phát hiện lúc khởi tạo, **trước khi ghi JSONL hoặc inventory**.
- **Kết thúc sớm:** gameplay kết thúc thì dừng ngay, ghi snapshot cuối và dòng `end`.

## C. File inputs

```json
{"frames":[
  {"tick":0,"move":[0,1]},
  {"tick":120,"move":[0,0],"catch":true},
  {"tick":121,"catch":false},
  {"tick":180,"interact":true},
  {"tick":181,"interact":false}
]}
```

- **`tick`:** nguyên không âm, tăng nghiêm ngặt.
  - Trước frame đầu, `move = [0,0]` và các nút là `false`.
  - Frame chỉ cập nhật trường có mặt.
  - Không có file inputs tương đương không điều khiển.
- **`move`:** gồm hai số hữu hạn trong `[-1, 1]`, chuẩn hóa nếu độ dài > 1. Thành phần thứ hai dương là xuống trong `gather` (`[x, d]`), về bắc trong `quan` (`[x, z]`).
- **Nút boolean:**
  - `interact`: cập bến hoặc hái trong `gather`; nấu, bưng hoặc phục vụ trong `quan`.
  - `catch`: bắt cá trong `gather`.

  Nút chỉ tác động ở **cạnh lên** (`false` → `true`). Hành động đúng kiểu nhưng sai pha thì **bỏ qua**.
- **Mã 2:** tên trường sai hoặc chưa hỗ trợ, kiểu sai, tick lặp hoặc giảm.

## D. File scenario (dựng tình huống để test)

Gốc chỉ nhận khối trùng mode. Ví dụ đặt nút đúng mép bán kính hái của preset:

```json
{"gather":{
  "player":{"pos":[20,0],"heading_deg":0},
  "hold":["ca_loc","bong_sung"],
  "nodes":[{"id":"N1","kind":"bong_dien_dien","pos":[22,0]}],
  "fish":[],
  "random_fish":false,
  "time_left_ticks":120
}}
```

| Khối / trường | Nội dung |
|---|---|
| `gather.player` | `pos, vel, heading_deg, oxygen_ticks, hp, zero_oxy_ticks, catch_cd_ticks`. Mặc định vị trí và hướng theo tuning, vận tốc `[0,0]`, oxy và Máu đầy |
| `gather.hold` | Mảng kind theo thứ tự nhặt (mới nhất ở cuối), mặc định rỗng |
| `gather.nodes[]` / `fish[]` | Nút `{id, kind, pos, regrow_ticks}` (0 là ready) · cá `{id, kind, pos, heading_deg}` (hướng mặc định 0°) |
| `gather` | `random_fish, time_left_ticks` |
| `quan.player` | `{pos, vel}`, mặc định vị trí theo tuning và `vel: [0,0]` |
| `quan.stock` / `hand` | `stock` là giá trị `items` ở mục G, **gồm cả phần giữ chỗ**. `hand` là payload món hoặc `null`, mặc định `null` |
| `quan.stoves[]` / `tables[]` | Bếp `{id, pos, state, dish, cook_ticks_left, ready_ticks}`; `state` là `idle` (mặc định), `cooking` hoặc `ready`; `ready_ticks` là tuổi món trên bếp, mặc định 0 khi ready. Bàn `{id, pos}`, người ngồi suy từ khách |
| `quan.customers[]` | `{id, table_id, dish_id, order_tick, state, patience_ticks_left, eat_ticks_left, order_status, reserved, base_price, tip}`; `reserved` là map kind → số lượng |
| `quan` | `time_left_ticks, random_customers, reputation`. Uy tín mặc định theo tuning |

*Ghi chú: ví dụ trên lab board bị cắt ở `nodes[0].pos`; `[22,0]` là suy ra từ câu "đặt nút đúng mép bán kính hái" (2.0 m tính từ `[20,0]`).*

**Thay thế và cập nhật danh sách:**
- `nodes`, `fish`, `customers` **thay thế** danh sách mặc định; `[]` là rỗng.
- `stoves`, `tables` **cập nhật theo id hiện có**.
- Id phải duy nhất trong mỗi mảng.

**Sắp xếp và cấp id:**
- Sắp id bằng khóa **(tiền tố, hậu tố số hoặc −1, id gốc)**. Tiền tố là phần trước dãy chữ số ASCII cuối id, hoặc toàn id nếu không có hậu tố. Chuỗi so theo mã Unicode, nên `F2` đứng trước `F10`.
- Id mới nối sau hậu tố lớn nhất của họ id tương ứng đã nạp hoặc đã phát trong lượt.

**Cờ `random_*`:** mặc định `true`.
- `random_fish: false` tắt cá mặc định; cá trong fixture đứng yên.
- `random_customers: false` tắt khách tự sinh, vẫn dùng khách trong fixture.

**Đồng hồ và bộ đếm:**
- `time_left_ticks` mặc định theo tuning; khi khai thì phải là số nguyên dương không vượt thời lượng pha.
- `phase_tick` bắt đầu từ 0; lịch khách tính theo `phase_tick`, kể cả khi rút ngắn ca.
- Bộ đếm chưa kích hoạt mặc định 0. `vel` là vận tốc tự bơi/đi đã chặn mép.
- Oxy trong `[0, max]`, Máu trong `[1, max]`. `zero_oxy_ticks` trong `[0, 59]`, chỉ dương khi oxy bằng 0 và người chơi đang dưới nước.

**Món và đơn:**
- Payload món là `{order_id, dish_id, base_price}`, với `order_id` bằng id khách.
- Khách mặc định ở trạng thái `waiting`, `order_tick: 0`, kiên nhẫn đầy, `order_status: reserved`.
- Trạng thái đơn: `reserved` / `assigned` / `unfulfillable` / `served`.
- Đơn `reserved` thiếu `reserved` thì cấp theo công thức, xét theo `order_tick` rồi id bàn.
- Đơn `assigned` có **đúng một** món ở bếp hoặc trên tay, phần giữ chỗ rỗng.
- Bếp `cooking` có timer dương và món khớp đơn.
- Khách `eating` phải ở đơn `served`, có timer ăn dương và khai `base_price, tip` đã chốt.
- Đơn `unfulfillable` vẫn chờ, phần giữ chỗ rỗng và không có món.

**Mã 2** khi:
- trường sai hoặc chưa hỗ trợ, khối sai mode;
- id trùng trong danh sách, id bếp/bàn cập nhật không tồn tại;
- tọa độ ngoài miền, liên kết thiếu, bộ đếm âm hoặc mâu thuẫn;
- giỏ quá trần, khai cả `quan.stock` và `--inventory`;
- nguyên liệu/món ngoài phạm vi, khách trùng bàn;
- giữ khác công thức hoặc giữ quá tồn;
- bếp và tay cùng giữ một đơn, hoặc món không khớp đơn.

Tham chiếu id không tạo thêm thực thể.

## E. Output JSONL

Mỗi dòng là một object JSON UTF-8.
- **Thứ tự ghi:** chụp snapshot ở **tick 0** sau khi dựng fixture, ở bội số của `--snapshot-every` và ở tick dừng.
- Mỗi tick tối đa một snapshot. Ghi event theo thứ tự xử lý rồi mới tới snapshot. Dòng `end` luôn cuối.

| Pha | Trường snapshot |
|---|---|
| Chung | `type:"snapshot", tick, sim_tick, mode, phase, phase_tick, state, time_left_ticks, money, earned, reputation, score`. `tick` là số bước ngoài, `sim_tick` là số bước gameplay toàn lượt, `state` là `playing` hoặc `finished` |
| gather | `player` theo D, thêm `oxygen_max_ticks, hp_max, at_surface`; `hold, hold_count, hold_capacity, nodes[], fish[]`. Nút có `ready` bằng `regrow_ticks == 0` |
| quan | `player, stock, hand, stoves[], tables[], customers[]` theo D. Bàn thêm `customer_id` (trống là `null`). Chỉ liệt kê khách còn ngồi |

Dòng event có dạng `{"type":"event","tick":1,"phase":"gather","name":...,"data":{...}}`.

| name | data |
|---|---|
| `gather` / `node_regrown` | `node_id, kind, amount` / `node_id` |
| `hold_full` | `action` (`gather`/`catch`), `node_id` hoặc `fish_id` tương ứng, `required, free` |
| `fish_caught` | `fish_id, kind, yield`; một event mỗi đàn, lấy đủ yield |
| `dive` / `surface` | `pos` sau di chuyển; chỉ phát khi đổi phía của biên mặt nước |
| `oxygen_empty` / `choke` | `oxygen_ticks: 0` khi vừa chạm 0 / `hp` sau khi trừ |
| `faint` | `cause: "choke", lost, hp: 0` |
| `gather_end` | `reason` (`time`/`docked`/`fainted`), `inventory` là object theo G |
| `customer_arrived` / `no_dish` | `order_id, table_id, dish_id` / `{}` khi có bàn mà thiếu món |
| `cook_started` / `dish_ready` / `dish_picked` | Mọi event có `stove_id, order_id, dish_id`. Bắt đầu nấu thêm `items, base_price` |
| `served` | `order_id, table_id, dish_id, patience_ticks_left, base_price, tip` |
| `paid` | `order_id, table_id, base_price, tip, amount, reason` (`finished_eating`/`closing`). `base_price` là tiền món trước boa |
| `customer_left` | `order_id, table_id, reason` (`patience`/`closing`), `reputation` |
| `quan_end` | `reason:"time", money, earned, shift_earned, reputation`. `money` là số dư, `earned` là tổng thu cả lượt, `shift_earned` là thu trong ca |

- `items` và `lost` trong event là **mảng kind**. `lost` theo thứ tự bỏ: nhặt sau bỏ trước (LIFO).
- **Dòng cuối:** `type:"end", ticks, sim_tick, mode, state, reason, money, earned, reputation, score`.
  - `reason` là `time`/`docked`/`fainted` cho gather, `time` cho quan, hoặc `tick_limit` khi gameplay chưa xong.
  - Kết thúc đúng bước cuối được cấp thì ưu tiên lý do gameplay.
- **Điểm** ở mọi snapshot và ở `end` = **`earned + 100 × floor(reputation)`**.
- **Sắp xếp:** mảng thực thể theo id; `hold` theo thứ tự nhặt; `cook_started.items` theo kind.
- **Làm tròn và so sánh:**
  - Xuất tọa độ đến 3 chữ số thập phân. So bán kính và tính giá **trước** khi định dạng.
  - So **chính xác** tiền, điểm, id, số lượng, countdown và lý do.
  - **Dung sai:** tọa độ ±0.1 m, uy tín ±0.01, thời gian ±2 tick.
  - Deadline, lịch, cạnh, thứ tự và tick của event dùng giá trị chính xác.
- **Tất định:** cùng bản chạy, máy, seed, tham số và nội dung đầu vào thì JSONL và file kho phải **giống nhau từng byte**.
  - Tách RNG giao diện và đồng hồ thực khỏi mô phỏng.
  - Duyệt ứng viên theo thứ tự cố định; id món so theo mã Unicode.
  - Chọn ngẫu nhiên nhất quán trong mỗi bản nộp. Fixture muốn dựng nhánh cụ thể thì đặt dữ liệu và tắt phần ngẫu nhiên liên quan.

## F. Luật bắt buộc khi xử lý một bước

**Chung:**
- **Một bước:** bước k đọc frame có `tick = k`, biến trạng thái k thành k+1 và ghi event tại **k+1**.
- **Đồng hồ:** mỗi bước tăng `sim_tick` và `phase_tick` một đơn vị; lịch dùng `phase_tick` sau khi tăng. Timer không âm.
- **Hồi chiêu và thực thể mới:** cooldown L đặt ở tick t thì dùng lại được từ t+L. Thực thể sinh ở cuối bước chỉ tham gia tương tác/di chuyển từ bước sau.
- **Khoảng cách:** dùng khoảng cách Euclid trên mặt phẳng của pha, **tính cả đúng mép bán kính**.
- **Vận tốc:**
  - Vận tốc hội tụ về `speed × move` trong tối đa `ramp_max_ticks`, rồi giữ đích. Tích phân với Δt = 1/60 s.
  - Chặn từng thành phần ở biên chữ nhật và triệt thành phần vận tốc hướng ra ngoài.
  - Vận tốc trong snapshot là vận tốc tự điều khiển sau khi chặn mép.
- **Hướng mặt:** theo `move` khác 0 gần nhất; đứng yên thì giữ hướng cuối.
- **Nội thất quán:** không cản đường.

**Gather**
1. **Đồng hồ:** tăng đồng hồ, giảm timer ca, hồi bắt và hồi nút. Nút từ 1 về 0 thì phát `node_regrown` (theo thứ tự id) và hái được ngay.
2. **Bơi và oxy:**
   - Bơi, chặn biên, so đầu và cuối bước để phát `dive` hoặc `surface`.
   - Tính oxy theo **d cuối bước**. Ở mặt nước (`d ≤ 0.5`): +6 tick oxy, kẹp tối đa và reset ngạt. Dưới nước: −1 tick, kẹp 0. Phát `oxygen_empty` khi oxy từ dương xuống 0.
3. **Ngạt và ngất:**
   - Mỗi bước dưới nước kết thúc với oxy 0, **kể cả bước vừa chạm 0**, thì tăng `zero_oxy_ticks`.
   - Đủ 60 thì đặt lại về 0, trừ 1 Máu, phát `choke`.
   - Máu về 0 thì bỏ giỏ theo LIFO, phát `faint` rồi `gather_end` với `fainted` và kho rỗng, dừng bước.
   - Chạm oxy 0 ở t và ở dưới nước liên tục thì ngạt lần đầu ở **t+59** (nếu đếm ban đầu là 0). Nổi lên đúng bước đáng lẽ ngạt thì hồi oxy và không ngạt.
4. **Cạnh `interact`:**
   - Xét bến trước, bằng khoảng cách tới tâm trên `[x, d]`. Trong bến thì kết thúc ngay `docked`.
   - Ngoài bến, chỉ hái khi ở mặt nước: chọn nút ready gần nhất trong bán kính, hòa thì theo id.
   - Đủ chỗ thì thêm 1 nguyên liệu, đặt `regrow_ticks = regrow_s × 60` và phát `gather`.
   - Thiếu chỗ thì phát `hold_full`, nút giữ nguyên.
5. **Cạnh `catch`:** chỉ khi đã hết hồi và đang dưới nước.
   - Chọn đúng đàn gần nhất trong bán kính, hòa thì theo id.
   - Đủ chỗ thì thêm **toàn bộ** yield, xóa đàn, phát `fish_caught`, đặt hồi `catch_cooldown_s × 60`.
   - Thiếu chỗ thì phát `hold_full`, giữ đàn và giữ nguyên cooldown, không thử đàn khác.
   - Không có đàn trong tầm thì không có sự kiện bắt và không tính hồi chiêu.
6. **Hết giờ:** timer ca về 0 thì kết thúc `time` ở mọi độ sâu, giữ giỏ sau các hành động trên.
   - Chốt kho ngay khi kết thúc và dừng xử lý.
   - E đúng mép bến ở bước cuối vẫn cho `docked` nếu còn Máu.
   - Ngoài bến, hái hoặc bắt hợp lệ ở bước cuối vẫn vào kho.

**Quán**
1. **Đồng hồ:** tăng đồng hồ, giảm timer ca, nấu, ăn và kiên nhẫn. Chỉ tăng `ready_ticks` cho món đã ready ở đầu bước.
2. **Bếp:** xét theo id. Món nấu xong chuyển sang ready với `ready_ticks = 0`. Dùng `burn_s: null`.
3. **Di chuyển rồi tối đa một `interact`:** chọn đối tượng theo **(khoảng cách, bếp trước bàn, id)**. Nếu đối tượng được chọn không tương tác được thì bỏ lượt.
   - **Bếp idle:** lấy đơn reserved cũ nhất theo `order_tick` rồi id bàn, tiêu đúng nguyên liệu đã giữ, chốt giá và bắt đầu nấu.
   - **Bếp ready:** giao món cho tay trống, bếp về idle.
   - **Bàn:** nhận đúng `order_id` thì khách ăn với timer đầy.
   - **Boa:** chốt bằng `floor(tiền món × tip_rate)` nếu tỷ lệ kiên nhẫn còn lại sau bước 1 đạt `tip_min_patience_ratio`; thấp hơn thì boa 0.
   - Phục vụ đúng tick kiên nhẫn về 0, hoặc lúc hết ca, vẫn hợp lệ.
4. **Thanh toán và khách rời:** xét theo id bàn.
   - Khách ăn xong trả tiền rồi rời bàn ngay.
   - Nếu ca còn giờ: khách `waiting` có kiên nhẫn 0 thì rời, uy tín đổi theo `left_reputation_delta`.
   - **Khi hết ca:** khách còn ăn trả ngay (kể cả vừa được giao món); khách còn chờ rời với `closing` và không trừ uy tín. Dọn xong thì phát `quan_end`.
   - Khi khách rời: nhả phần giữ thô, bỏ món của đơn đang nấu, đang ready hoặc trên tay. Nguyên liệu đã dùng không hoàn lại.
   - Boa dương thì cộng `tip_reputation` khi thu tiền. Kẹp uy tín theo tuning.
5. **Khách mới:** nếu còn giờ, xét lượt khách ở `first_customer_tick`, rồi mỗi `customer_interval_s × 60` tick.
   - Không còn bàn trống thì bỏ lượt; có bàn thì lấy bàn trống id nhỏ nhất.
   - **Chọn đều theo seed** trong 3 món đủ nguyên liệu khả dụng (tồn vật lý trừ phần giữ). Không món nào đủ thì phát `no_dish`.
   - Khách mới giữ đúng công thức ngay, `order_tick` bằng `phase_tick` hiện tại, kiên nhẫn đầy và bắt đầu giảm từ bước sau.

## G. File kho (hợp đồng tích hợp Lặn & Hái → Mở Quán)

```json
{"items":{"bong_sung":2,"ca_loc":1}}
```

- **Schema:**
  - File chỉ có khóa `items`, là object kind → số nguyên không âm. Kind vắng mặt tính là 0.
  - Bên ghi bỏ các khóa có lượng 0. Kho rỗng là `{"items":{}}`.
  - Bên đọc từ chối sai schema, kind lạ và giá trị ngoài miền (mã 2).
  - Trần giỏ không áp lên kho quán.
- **Khi nào ghi:**
  - File chỉ chứa hàng trong giỏ khi có `gather_end` và phải khớp object `inventory` trong event đó.
  - `gather --inventory-out` ghi **đúng một lần**; ngất thì ghi kho rỗng.
  - Chạm `--ticks` trước khi buổi sáng kết thúc thì không tạo và không ghi đè file.
  - Ghi file tạm cùng thư mục, rồi thay thế nguyên tử sau khi ghi thành công.
- **Quán chạy độc lập:** thiếu cả inventory lẫn `scenario.quan.stock` thì kho rỗng. Tiền và `earned` đầu lượt độc lập bằng 0. Uy tín theo tuning, trừ khi scenario quán có khai.

**Smoke test hộp đen:**
- Dùng preset ở A, tạo `dock.json` là `{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}` và `dock-inputs.json` là `{"frames":[{"tick":0,"interact":true}]}`.
- Snapshot quán ở tick 0 phải có `stock: {"bong_sung":2,"ca_loc":1}`, đúng file mà tiến trình đầu ghi.
- Hai lệnh:

```
<headless_cmd> --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json --ticks 1 --inventory-out kho.json --out r.jsonl
<headless_cmd> --mode quan --seed 42 --inventory kho.json --ticks 0 --out q.jsonl
```

*Ghi chú: hai lệnh trên lab board bị cắt ngang; phần đuôi ở đây được dựng lại theo `tests/test_smoke_p1.py::test_inv_01_gather_writes_inventory_quan_reads_it`.*

---

## Chỗ PRD chưa nói rõ (cần hỏi Anh Năm / ghi `docs/clarify.md`)

1. Đơn chuyển sang `unfulfillable` khi nào? PRD chỉ mô tả trạng thái này trong scenario (vẫn chờ, giữ chỗ rỗng, không có món).
2. `paid.amount` có bằng `base_price + tip` không?
3. Hết ca đúng tick khách ăn xong thì `paid.reason` là `finished_eating` hay `closing`? Bước 4 xét "ăn xong" trước, nên nhiều khả năng là `finished_eating`.
4. `no_dish` có tiêu bàn hay không? Theo bảng sự kiện thì không có khách nào được tạo.
