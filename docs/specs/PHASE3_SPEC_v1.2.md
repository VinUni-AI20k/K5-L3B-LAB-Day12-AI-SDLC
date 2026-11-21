# PHASE 3 — IMPLEMENTATION SPECIFICATION
## Quán Ăn Chợ Nổi · TICKET-03 «Mùa Nước Nổi» · Test Contract v1.2

> **Mục đích:** Đặc tả cho nhóm 5 người và coding agents (Codex/Gemini) triển khai *breaking change* kho cá thể + độ tươi ở Phase 3. Đây là bản tổ chức lại yêu cầu, **không phải tài liệu chính thức thay thế TICKET-03**.
>
> **Thứ tự ưu tiên:** `TICKET-03_original.md` (v1.2) → `TICKET-02_original.md` (v1.1, những chỗ chưa bị thay) → `PRD-0_original.md` (v1.0, những chỗ chưa bị thay). Tài liệu này và `PHASE2_SPEC_v1.1.md` chỉ là hướng dẫn triển khai/diễn giải. Nếu có xung đột, quay về nguồn chính thức.
>
> **Repo tham chiếu:** https://github.com/miao1114/K5-L3B-LAB-Day12-AI-SDLC-CodexGemini  
> **Thời gian lab:** 35 phút, mốc 1:55–2:30. Tag bàn giao `phase-3` trên `main`.  
> **Đối tượng:** Nhóm 5 người, đặc biệt các tác vụ P3-01–P3-05.

---

## 0. Hướng dẫn bắt buộc cho AI coding agent

1. Đọc đủ **ba nguồn gốc** trên, `AGENTS.md` (nếu có), `README.md`, `game.contract.json`, source thực tế, test hiện có và `git status` trước khi sửa. **Không mặc định repo hiện tại vẫn giống Phase 1/2.**
2. Phân tích tác động lên schema/adapter, Gather, Quán, `day`, CLI/scenario/JSONL, UI và fixtures. Ghi quyết định chuyển schema tại `docs/adr/ADR-003-inventory-freshness.md` (mẫu có sẵn).
3. Không phá luật v1.1 còn hiệu lực: 60 tick/s, cá bơi/sinh, cá sấu, 2 bếp/4 bàn/6 món, `day`, Shop, pause, thứ tự input/event/timer. **Chỉ thay các phần TICKET-03 đánh dấu thay thế hoặc bổ sung.**
4. Không duy trì việc chấp nhận **kho đếm** trong chế độ chấm v1.2. Có thể dùng adapter tương thích tạm ở nhánh dev trong lúc chuyển, nhưng cuối cùng `contract_version:"1.2"` phải từ chối kho đếm với mã thoát **2**.
5. Không làm tròn `fresh` trước khi so mốc 30 hoặc tính `floor` giá. Không dùng clock render hoặc random UI để thay đổi simulation; các cùng input/seed phải deterministic.
6. Chỉ triển khai extension `current` / `reservations` khi **nhóm quyết định bật**. Extension không được làm thay đổi kết quả core/headless khi tắt.
7. Không reset hard, force push, ghi đè commit của thành viên khác, xóa test thất bại, tự merge/tag nếu chưa được giao. Ghi bằng chứng thật và báo cáo BLOCKED/PARTIAL trung thực.

## 1. Mục tiêu và phạm vi lõi

Nguyên liệu phải có **danh tính** và **độ tươi riêng** từ lúc hái/bắt, trong giỏ, qua file kho/day đến khi được lấy khỏi kho để nấu. Nguyên liệu ươn vẫn tồn tại và chiếm chỗ nhưng không dùng nấu. Khi nấu, giá chốt theo độ tươi **thực tế của từng cá thể đã tiêu**. Cả web HUD, headless events và snapshot phải phản ánh điều này.

**Điều kiện bàn giao lõi**:

- Manifest `contract_version: "1.2"`, thêm `freshness` đúng tham số.
- Kho cá thể v1.2 xuyên `gather --inventory-out` → `quan --inventory`, và trong `day` không qua file; kho đếm v1.0/v1.1 bị từ chối.
- ID cá thể unique, cấp đúng thứ tự, giữ nguyên qua chuyển pha; không cấp lại ID đã mất/dùng; xử lý Day fixture theo quy tắc nguồn.
- Gather hao tươi 0.5/s, Quán 0.25/s, ngưỡng ươn `<30`, `spoiled` một lần đúng tick, pause không hao.
- Quán giữ nguyên liệu theo ID, chọn tươi nhất, làm lại giữ chỗ khi một món giữ vừa ươn, tính giá theo độ tươi và tiền boa theo giá đã chốt.
- Scenario/snapshot/events/validation v1.2; UI chỉ hiển thị trạng thái mô phỏng, thấy được độ tươi hoặc hàng ươn.
- Smoke hai tiến trình và Day; regression P1/P2 còn hiệu lực; tài liệu tác động, CHANGELOG, verification và proof; `phase-3` đúng hạn.

**Không thuộc lõi:** Dòng nước lũ `current`, Khách đặt trước `reservations`; xem mục 11.

## 2. Kho cá thể v1.2 — Hợp đồng giao tiếp bắt buộc

### 2.1 Schema duy nhất khi chạy v1.2

```json
{
  "items": [
    {"id": "I1", "kind": "ca_linh", "fresh": 100},
    {"id": "I2", "kind": "ca_loc", "fresh": 97.5}
  ]
}
```

Kho rỗng là **`{"items":[]}`**. Root có **đúng một khóa** `items`; giá trị **mảng cá thể**, không phải object đếm. Mỗi cá thể có `id`, `kind`, `fresh`:

| Trường | Hợp lệ | Không hợp lệ |
|---|---|---|
| `id` | string khác rỗng, unique giữa các cá thể vật lý | rỗng, không phải string, ID trùng |
| `kind` | một trong 6 nguyên liệu hợp lệ từ v1.1 | kind chưa định nghĩa |
| `fresh` | số hữu hạn trong `[0,100]` | âm, >100, NaN/Infinity, sai kiểu |

Các nguyên liệu: `ca_loc`, `ca_linh`, `ca_keo`, `bong_dien_dien`, `bong_sung`, `keo_neo`.

**Ràng buộc thêm:**

- V1.2 đọc file kho đếm cũ (ví dụ `{"items":{"ca_loc":1}}`) → **exit code 2**. Không tự chuyển ngầm.
- `quan` nhận nguyên số lượng, ID và fresh, **kể cả hàng đã ươn**. Sức chứa giỏ chỉ áp lên **giỏ**, không áp lên kho quán.
- Không được sinh thêm cá thể chỉ vì chuyển file, giữ chỗ, mở Quán, chụp snapshot hoặc cập nhật HUD.
- Sắp hàng **xuất file theo ID**. Đừng dùng thứ tự xuất file để thay thế thứ tự nhặt của giỏ khi xử lý LIFO. Cần giữ hai semantics riêng.
- Cần đảm bảo lưu/đọc `fresh` đủ chính xác để nhánh so mốc 30 và công thức `floor` không đổi vì làm tròn.

### 2.2 Vòng đời ID

- ID do hệ thống cấp **`I1`, `I2`, ...` theo thứ tự vào giỏ** (với catch yield nhiều cá thể, cấp một ID cho mỗi cá thể).
- Tiếp tục tăng **xuyên pha và Ngày**, kể cả ID cũ đã tiêu, bỏ hoặc bị rơi.
- Trong `scenario.day`: **Ngày đầu** giữ ID của `gather.hold` fixture; **các Ngày sau** dùng ID mới cấp theo thứ tự mảng khi dựng lại mẫu `hold`.
- ID cá thể vật lý không được xuất hiện đồng thời như hai vật thể khác nhau. `customers[].reserved` chỉ là **tham chiếu danh sách ID** tới hàng trong `quan.stock`, không phải bản sao hàng vật lý.
- Trong chế độ day, khi bàn giao kho trong cùng tick giữa hai pha, ID và fresh **không đổi**, Quán bắt đầu gameplay từ bước sau.

### 2.3 Ghi file kho và trường hợp kết thúc

- `gather --inventory-out` ghi **đúng một lần** khi có `gather_end` (`docked`, `time`, `fainted`).
- Ghi file tạm cùng thư mục, sau khi thành công thì **atomic replace** vào đích.
- `fainted` → kho rỗng `{"items":[]}`; `gather_end.data.inventory` đồng bộ.
- CLI dừng do chạm `--ticks` **trước** khi gather kết thúc → **không tạo, không ghi đè** file inventory-out có sẵn.
- `gather_end.data.inventory` cũng dùng schema wrapper `{"items":[...]}`.

### 2.4 Sự khác biệt v1.1 → v1.2

```text
v1.1: {"items":{"ca_loc":1,"bong_sung":2}}
           ↓ BREAKING CHANGE
v1.2: {"items":[
          {"id":"I1","kind":"ca_loc","fresh":100},
          {"id":"I2","kind":"bong_sung","fresh":100},
          {"id":"I3","kind":"bong_sung","fresh":100}
       ]}
```

**KHÔNG** thay đổi recipe của sáu món, chỉ thay **cách đại diện từng đơn vị nguyên liệu** và cách tính giá dựa trên chúng.

## 3. Độ tươi — số liệu và độ chính xác

| Tham số | Giá trị chính thức | Quy đổi 60 Hz |
|---|---:|---:|
| fresh ban đầu khi nhặt | `100` | áp ngay tick thu thập |
| hao trong giỏ (Gather) | `0.5` điểm/s | `1/120` điểm/tick |
| hao trong kho Quán | `0.25` điểm/s | `1/240` điểm/tick |
| ươn | `fresh < 30` | kiểm bằng **giá trị thật**, không làm tròn |
| sàn độ tươi | `0` | clamp về 0 |

**Điểm quan trọng:**

- Hàng **đã có ở đầu bước** mới hao trong Gather; cá/rau **mới bắt/hái** có fresh=100 và **bước sau** mới bắt đầu hao.
- Quán giảm độ tươi kho thô trong bước timer **trước khi** làm lại giữ chỗ và trước khi bếp bắt đầu nấu trong chính bước đó.
- Hàng **đã được giữ cho khách vẫn hao tươi** vì vẫn là hàng thô trong kho; món đang nấu/đã chín không còn là hàng thô trong kho và không hao tươi.
- Pause dừng sim_tick, phase_tick, các timer gameplay và độ tươi; cạnh resume chạy gameplay ngay theo luật v1.1.
- Độ tươi bằng **30** vẫn hợp lệ để nấu. Khi từ `≥30` sang `<30`, phát **một** event `spoiled` cho cá thể đó. Nhiều cá thể cùng vượt ngưỡng → sắp theo ID.
- Gợi ý số học từ nguồn: có thể dùng đơn vị **240 phần của một điểm** (Gather -2 đơn vị/tick, Quán -1/tick) khi fixture biểu diễn chính xác. Với đầu vào khác cần bảo đảm đủ độ chính xác; không được làm tròn làm đổi nhánh ngưỡng hoặc floor.

**Một edge case dễ sai:** Cá thể stock ban đầu fresh=100, nếu người chơi nấu ở **tick gameplay đầu tiên**, Quán giảm tươi trước tương tác. Tại lúc nấu fresh = `100 - 1/240`; giá `ca_loc_nuong_trui` niêm yết 60 sẽ là `floor(60 × (100 - 1/240)/100) = 59`, **không phải 60**. Đừng áp nguyên giá niêm yết chỉ vì fixture bắt đầu ở 100.

### 3.1 Event `spoiled`

```json
{"type":"event","tick":1,"phase":"gather","name":"spoiled",
 "data":{"item_id":"I1","kind":"ca_linh","location":"hold"}}
```

- Trường bắt buộc: `item_id`, `kind`, `location` = `hold` hoặc `stock`.
- Event chỉ xuất hiện khi **vừa vượt ngưỡng**, không lặp mỗi tick sau khi đã ươn.
- Trên Gather, event decay diễn ra sớm trong bước; trên Quán, xuất toàn bộ spoiled theo ID **trước** khi xử lý đặt giữ lại nguyên liệu.

### 3.2 Fixture kiểm ngưỡng chính thức

```json
{
  "gather": {
    "hold": [{"id":"I1","kind":"ca_linh","fresh":30}],
    "random_fish": false,
    "monsters": []
  }
}
```

Chạy một tick không input, `spoiled` xuất hiện tại tick 1. Fixture `fresh=29.9` phải không phát spoiled nữa nếu không có chuyển ngưỡng từ `≥30`.

## 4. Gather — tương tác, decay, rơi đồ và xuất kho

Kế thừa toàn bộ v1.1: di chuyển/oxy, cá 3 loài bơi và sinh, cá sấu/hit, các nút cây, capture, Day upgrades, tùy chọn extension. Chỉ đổi cách đại diện giỏ và thêm độ tươi/event.

### 4.1 Luồng cập nhật một tick Gather (đúng thứ tự v1.2)

1. Tăng đồng hồ, giảm cooldown, hồi cây và **hao tươi những nguyên liệu đã có trong giỏ ở đầu bước**; phát `spoiled` nếu qua ngưỡng.
2. Nếu bật extension dòng lũ, xử lý lịch `current`.
3. Bơi, oxy, ngạt.
4. Nếu bật Lao, xử lý tấn công; sau đó quái vật cập nhật theo ID và xét tối đa một hit.
5. Xử lý `interact`: kiểm bến **trước** nút hái.
6. Xử lý `catch`, rồi `photo` nếu extension có bật.
7. Kiểm tra hết giờ (kết thúc ca ngay khi đúng điều kiện).
8. **Chỉ khi còn giờ**: cá bơi, sinh đàn theo lịch, cập nhật Cá Hô nếu bật.

**Faint:** Nếu HP=0 sau choke hoặc monster_hit: rơi **toàn bộ cá thể còn lại** theo LIFO, phát `faint`, rồi `gather_end(fainted)` ngay; không chạy bước sau của tick đó. Khi monster_hit: rơi `floor(len(hold)/2)` cá thể theo LIFO, event lost liệt kê object item theo thứ tự bỏ.

### 4.2 Hái/bắt và ID

- Hái/catch thành công cấp `I#` từng cá thể, đặt fresh=100; catch loài cá với yield 2/3 tạo đủ số object.
- Nguyên liệu ươn vẫn trong giỏ, chiếm 1 ô/cá thể, có thể bị rơi khi trúng quái; Gather không tự xóa vì ươn.
- LIFO dựa trên **thứ tự nhặt**, không dựa trên ID sort trong file kho.
- `gather_end` chuyển **những gì còn trong giỏ** nếu `docked/time`, kể cả đồ ươn; `fainted` đưa kho rỗng.

## 5. Quán — decay, giữ chỗ, nấu, tính giá và thanh toán

### 5.1 Cách lưu kho và giữ chỗ

- `quan.stock` = mảng các object item có ID/fresh, bao gồm cả hàng **đang được giữ chỗ** và hàng ươn.
- `customers[].reserved` = mảng **ID string** của những item đang được giữ cho order; không phải map kind → quantity.
- Mỗi ID trong `reserved` phải trỏ đến item đang tồn tại trong `stock`, chưa ươn, đúng công thức và **không bị hai đơn giữ cùng lúc** (khi khởi tạo fixture).
- Để chọn nguyên liệu cho mỗi loại trong recipe: trong số item còn khả dụng `fresh ≥30`, lấy các item **tươi nhất trước**, hòa theo **ID**. Một đơn phải lấy đủ tất cả loại yêu cầu thì mới có thể giữ hợp lệ.
- Nếu fixture khai `order_status: reserved` mà bỏ `reserved`, tự cấp nguyên liệu theo thứ tự `(order_tick, table_id)` và quy tắc chọn tươi nhất/id. Fixtures sai hoặc mâu thuẫn → exit code 2.

### 5.2 Nguyên liệu vừa ươn khi đã giữ

Sau khi stock decay, phát toàn bộ `spoiled` theo ID. Rồi xử lý các đơn có item `reserved` vừa bị ươn theo **`order_tick` → ID bàn**:

1. Nhả **toàn bộ** IDs của đơn đó ra khỏi phần giữ.
2. Thử giữ lại **đúng một lần** bằng nguyên liệu khả dụng còn tươi, chọn tươi nhất rồi ID.
3. Nếu giữ đủ → đơn tiếp tục `reserved` với danh sách ID mới.
4. Nếu không đủ → **đơn thường** chuyển `unfulfillable`, không giữ cá thể nào nữa, khách vẫn chờ đến hạn. Không tự làm khách rời ngay.

Không nhả phần giữ khi item vẫn `fresh == 30`; chỉ trigger khi item thực sự qua ngưỡng. Đơn không bị ảnh hưởng không nên bị giữ lại vô cớ.

Nếu bật extension `reservations`, trường hợp khách đặt trước thất bại stock có quy tắc riêng ở mục 11, không áp logic khách thường cho đơn đặt trước.

### 5.3 Khi bếp bắt đầu nấu — P3-04

Kế thừa v1.1 về tương tác, chọn đơn cũ nhất, nấu B1/B2, lấy món, phục vụ T1–T4, countdown, đóng ca và tiền/uy tín. Thay đổi khi `cook_started`:

1. Lấy order trạng thái `reserved` hợp lệ, theo `order_tick`, hòa ID bàn.
2. Lấy **chính xác các item ID** đang giữ trong `customers[].reserved`. Không tự thay bằng item khác, không tiêu item của đơn khác.
3. Phải đúng recipe cả về `kind` và số lượng; item tại thời điểm nấu còn fresh `≥30` (thứ tự trước nấu đã xử lý spoiled/re-reserve).
4. Tính `mean_fresh = sum(item.fresh) / N` trên **tất cả cá thể vật lý được tiêu**, không phải trung bình các loại nguyên liệu.
5. Chốt `base_price = floor(menu[dish_id].price × mean_fresh / 100)` tại tick bắt đầu nấu, sau khi decay kho trong tick đó.
6. Ghi `base_price` vào payload món bếp/hand và dùng giá đó cho toàn bộ phục vụ/thanh toán; không tính lại khi món chín hay khách ăn.
7. Ghi `cook_started.data.items` = **mảng object item đã tiêu**, sắp theo `kind` rồi `id`.
8. Xóa các vật phẩm đã tiêu khỏi `stock` và giải phóng danh sách `reserved` theo luật `assigned`. Không để ID trùng vật lý và không hoàn nguyên liệu đã tiêu nếu khách rời.

**Mẫu tính giá:** với `goi_bong_sung`, hai cá thể có fresh **tại tick nấu** là 80 và 70 → average=75, `floor(40×0.75)=30` (nghìn đồng). Nếu stock fixture bắt đầu 80/70 trước tick tương tác thì **còn hao tươi** tại bước trước khi nấu, vì vậy giá có thể là 29; test cần đặt dữ liệu/time để phản ánh đúng thứ tự.

### 5.4 Phục vụ, tiền boa và điểm

- `tip = floor(base_price × 0.2)` nếu lúc phục vụ còn ≥50% kiên nhẫn, ngược lại =0 (thừa hưởng v1.1).
- Thanh toán khi ăn xong/closing: `amount = base_price + tip` (nguyên nghìn đồng), cộng đúng một lần vào `money`, `earned`, `shift_earned`; nếu tip>0 thì uy tín +0.2 (clamp [0,5]).
- `score = earned + 100 × floor(reputation)`.
- Món đã chín và món đang mang **không hao tươi**; giá không đổi khi khách phải chờ.
- Không re-reserve các order `assigned/served`, chỉ áp cho order còn phần giữ. Hủy món đúng đơn nếu khách rời, không tạo hàng vật lý trở lại.

### 5.5 Luồng một tick Quán (v1.2)

1. Đồng hồ và các timer.
2. **Hao tươi kho thô**, phát toàn bộ `spoiled` theo ID.
3. Xử lý lại giữ chỗ của các đơn bị ươn theo `order_tick`, rồi ID bàn.
4. Xét món chín/cháy (nếu extension burn bật), theo ID bếp.
5. Di chuyển, xử lý tối đa một tương tác (`E` cạnh lên), theo khoảng cách, bếp trước bàn, ID.
6. Thanh toán, hết kiên nhẫn và đóng ca theo luật v1.1.
7. Nếu vẫn còn giờ: xử lý khách đặt trước (nếu bật extension) rồi khách thường theo lịch.

**Boundary:** Phục vụ ở tick kiên nhẫn vừa chạm 0 hoặc tick hết ca **vẫn hợp lệ**. Phần thu tiền ở tick đóng ca xảy ra theo luật closing v1.1.

## 6. Day, Shop, pause và bàn giao

- Thứ tự chính v1.1: `DayIntro → gather → EveningIntro → quan → DayResult → Shop → ngày tiếp/summary`; headless day pha gameplay gồm `gather`, `quan`, `shop`.
- `gather_end` → `phase_start(quan)` **trong cùng tick**. Không decay thêm khi chuyển pha; gameplay Quán từ bước tiếp theo.
- Những thứ xuyên ngày vẫn giữ theo v1.1: `money`, `earned`, `reputation`, `upgrades`; oxy/Máu reset theo active level, giỏ mới, kho dư bị bỏ sau Shop.
- Mọi cá thể mới của ngày sau có ID **không trùng** với ngày trước; Day fixture Ngày đầu giữ ID đã cho, các ngày sau làm mới ID theo thứ tự mảng.
- Khi pause, **không hao độ tươi**. Shop giữ nguyên liệu thô dư nhưng **không hao tươi**; snapshot Shop biểu diễn stock mảng cá thể.
- Nếu bật `vendor` từ extension v1.1: hàng mua chuyển riêng sang kho Quán ngày sau với fresh=100 và ID mới; hàng bán phải chọn cá thể chưa ươn tươi nhất thuộc loại, hòa theo ID. Mọi hành vi `vendor` chỉ áp dụng nếu extension được bật và cấu hình hợp lệ.

## 7. Test Contract v1.2 — Manifest, CLI, scenario, output

### 7.1 Manifest

`game.contract.json`:

```json
{
  "contract_version": "1.2",
  "freshness": {
    "initial": 100,
    "gather_decay_per_s": 0.5,
    "quan_decay_per_s": 0.25,
    "spoiled_below": 30
  }
}
```

**Đây là đoạn minh họa các trường được thêm/đổi, KHÔNG phải toàn bộ manifest.** Giữ nguyên các khóa bắt buộc của v1.1, các số liệu 2 bếp/4 bàn/6 món, mode day, Shop, extensions đã chọn; cập nhật test/config theo manifest thật.

### 7.2 CLI và validation

Giữ CLI v1.1 (`--mode gather|quan|day --seed ... [--scenario] [--inputs] [--inventory] [--inventory-out] [--days] --ticks --out [--snapshot-every]`), quy tắc mode cho từng flag, exit codes 0/1/2. Không thay CLI để làm lối đi riêng cho v1.2.

- Khi v1.2: kho đếm cũ phải mã 2; file sai schema/id trùng/fresh không hữu hạn/out of range/kind lạ → mã 2.
- Fixture `gather.hold`, `quan.stock` là mảng item object; `customers[].reserved` là mảng IDs, không còn map số lượng.
- Scenario Day: giữ ID fixture ngày 1; cấp ID mới ngày sau như mục 2.2; tránh trùng ID giữa các nơi chứa.
- Kiểm tra dữ liệu có thể xác định từ đầu trước khi ghi JSONL hoặc inventory; fixture mâu thuẫn → mã 2.

### 7.3 Snapshot và event

Giữ toàn bộ field/timing của v1.0/v1.1, chỉ thay/đổi:

| Dữ liệu | v1.2 |
|---|---|
| `gather.hold` trong snapshot | mảng object `{id,kind,fresh}` |
| `quan.stock`, `shop.stock` trong snapshot | mảng object `{id,kind,fresh}` |
| `customers[].reserved` | mảng string ID |
| `gather_end.data.inventory` | `{ "items": [item objects...] }` |
| `cook_started.data.items` | mảng item object, sort theo `kind`, sau đó `id` |
| `monster_hit.data.lost` / `faint.data.lost` | mảng item object theo LIFO |
| event mới `spoiled` | `{item_id,kind,location:"hold"|"stock"}` |

Tất cả các `event` khác như `cook_started`, `dish_ready`, `served`, `paid`, `quan_end`, `phase_start`, `shop_end`, ... giữ hợp đồng v1.1 trừ khi TICKET-03 nói khác.

- Dung sai quan sát fresh ±0.01, nhưng **ngưỡng 30, floor, tick event biên** phải đúng ở cấp xử lý thực tế.
- Cùng code/máy/seed/flags/input → output deterministic, byte-identical như yêu cầu cũ.
- JSONL snapshot tick 0, theo bội `--snapshot-every` và tick dừng; event trước snapshot, `end` luôn dòng cuối; `--ticks 0` chỉ dựng fixture, không decay.

## 8. Chia việc 5 người và hợp đồng tích hợp (đề xuất nội bộ)

| Task | Chủ trách nhiệm | Phạm vi | Không tự ý thay |
|---|---|---|---|
| P3-01 | Người 1 | Gather hold itemization, decay, `spoiled`, hit LIFO | ID generator shared, validator shared |
| P3-02 | Người 2 | Contract v1.2/adapter, ID allocator, file IO, Day bridge, fixtures | Logic nấu/giữ chỗ |
| P3-03 | Người 3 | Quan stock decay, reservation by IDs, re-reserve, unfulfillable | Giá chốt/serve/payment |
| P3-04 | Người 4 | Cook consumes IDs, freshness price, events/payload, tip/payment | Stock selection/re-reserve |
| P3-05 | Người 5 | Web HUD freshness/spoiled, UI compatibility, integration proofs | Headless gameplay law |

**Interfaces phải chốt ở 7 phút đầu:**

1. Kiểu item và allocator `next_item_id` (phạm vi lifespan/Day/fixture). Ai quản lý quyền cập nhật `game.contract.json`.
2. `gather.hold` item objects và export inventory wrapper; thứ tự hold LIFO vs file sort.
3. `quan.stock` **mảng item**, `customers[].reserved` **mảng IDs**, owner của re-reserve, owner của consumed IDs.
4. Giá chốt: người 4 đọc `fresh` **sau** decay Quán trong tick, trước nấu, không tin giá cũ.
5. Snapshot/UI: người 5 chỉ đọc state, không hao tươi ở client.
6. Khi người 2 chuyển sang schema v1.2, smoke file và day phải chạy cùng commit trước khi gắn tag.

Mẫu chi tiết ở `docs/contracts/quan-freshness-interface.md`; sơ đồ chuyển đổi và thứ tự merge ở `docs/adr/ADR-003-inventory-freshness.md`.

## 9. Ma trận test tối thiểu (đề xuất để chứng minh DoD)

| ID nội bộ | Điều kiện / fixture | Kết quả cần đối chiếu |
|---|---|---|
| P3-T01 | Gather hold I1 fresh=30, 1 tick | `spoiled` đúng tick 1, location `hold` |
| P3-T02 | Gather hold I1 fresh=29.9, 1 tick | Không phát thêm `spoiled` |
| P3-T03 | Hái/catch tạo mới | fresh=100 lúc tạo, ID riêng, không hao trong bước nhặt |
| P3-T04 | Gather monster_hit với 5 items | Rơi floor(5/2)=2 theo LIFO, lost là item objects |
| P3-T05 | Gather faint | `{"items":[]}` khi kết thúc, lost đủ cá thể còn lại |
| P3-T06 | Gather dock→file→Quan tick0 | ID/kind/fresh bảo toàn, không decay thêm trong lúc truyền |
| P3-T07 | File kho đếm cũ | exit code 2, không output không hợp lệ |
| P3-T08 | ID trùng, fresh -1, 101, NaN, kind lạ | exit code 2 từng lỗi |
| P3-T09 | Quan stock có reserved item fresh=30 ở tick 0 | Tick1 spoiled rồi re-reserve theo thứ tự |
| P3-T10 | Quan re-reserve thiếu stock | `unfulfillable`, empty reserved, khách tiếp tục chờ |
| P3-T11 | Có nhiều item cùng kind khác fresh | Chọn tươi nhất, hòa ID |
| P3-T12 | Cook ở tick1, input stock ca_loc fresh100 | Giá floor sau decay = 59, consumed ID đúng |
| P3-T13 | Nấu 2 bếp đồng thời, nhiều khách | Không double-consume ID, event/snapshot đúng |
| P3-T14 | Serve/paid | Tip floor trên **giá đã chốt**, không dùng list price |
| P3-T15 | Quan stock decay khi pause | Không giảm fresh trong các bước paused |
| P3-T16 | Day 2+ fixture | ID tăng xuyên Ngày, không tái dùng; đổi pha không decay |
| P3-T17 | Shop stock | giữ schema item và không hao tươi trong Shop |
| P3-T18 | Re-run cùng seed/input | JSONL & inventory giống nhau byte-for-byte |
| P3-T19 | UI local | thấy độ tươi hoặc nhãn ươn, gameplay thực, không crash |

**Test kế thừa:** cá bơi/sinh, cá sấu, six menu, 2 stoves/4 tables, day/Shop, pause, timer/order events. Test nào cần sửa do schema breaking phải ghi giải thích `CHANGELOG.md` hoặc verification; **không xóa im lặng**.

## 10. Lịch tích hợp 35 phút và Definition of Done

| Mốc | Việc |
|---|---|
| 0–7 | Impact analysis, ADR, chốt schema và owners, xác định các test chuyển đổi |
| 7–20 | Adapter/allocator + Gather + Quan + Kitchen + HUD song song; tích hợp lần đầu; smoke ở phút 20 |
| 20–25 | Sửa blocker, smoke file→Quan và `day`, điều người rảnh sang giúp lát trễ |
| 25–32 | Bật contract v1.2 trên bản tích hợp; regression P1/P2 hợp lệ; verification, CHANGELOG, proof và retro |
| 32–35 | Dự phòng; gắn/push tag `phase-3` trước 2:30 |

**Checklist DoD:**

- [ ] Manifest v1.2 và freshness 100/0.5/0.25/30.
- [ ] Kho file/snapshot/day theo items[]; mã 2 với kho đếm và fixture invalid.
- [ ] ID duy nhất, cấp đúng thứ tự xuyên Ngày, LIFO đúng.
- [ ] Gather/Quan decay đúng tick, spoiled 1 lần, pause không decay.
- [ ] Re-reserve theo IDs/fresh, giá chốt theo trung bình từng cá thể.
- [ ] Cook/paid/tip/score đúng, không double-consume/thanh toán trùng.
- [ ] UI thấy freshness/spoiled.
- [ ] Smoke file và day có proof lưu `docs/proof/phase-3/`.
- [ ] ADR/impact + `CHANGELOG.md` breaking change; verification với AC → proof → PASS/PARTIAL/FAIL.
- [ ] Regression còn hiệu lực đạt; commit có đóng góp từ cả nhóm.
- [ ] Tag `phase-3` trỏ đúng commit tích hợp trên main, đẩy đúng hạn.

## 11. Extensions tùy chọn — chỉ làm sau khi core ổn định

### 11.1 Dòng nước lũ (`current`)

- Các mốc `t=1800*k`, k≥1: cảnh báo ở `t−120`; bắt đầu trước di chuyển ở `t`, kéo dài 480 tick [t,t+479].
- Hướng +x hoặc -x theo seed tại lúc bắt đầu; áp 1.5 m/s lên người chơi nếu **d ở đầu bước ≥10**, rồi clamp biên. Không tích lũy lực vào player.vel; cá và thủy quái không bị đổi chuyển động.
- Kết thúc lúc t+480: `current_end` reason `elapsed` trước di chuyển; nếu ca kết thúc giữa dòng lũ thì `phase_end` trước faint (nếu có) và gather_end. Nếu bắt đầu trùng tick cuối, vẫn có lực.
- Manifest `gather.current`: `interval_ticks`, `duration_ticks`, `warning_ticks`, `min_depth`, `speed`; scenario có `random_current:false` hoặc `current_direction` -1/+1; snapshot `current` null hoặc `{direction,ticks_left}`.
- Events: `current_warning {starts_at_phase_tick}`, `current_start {direction,duration_ticks}`, `current_end {direction,reason}`.

### 11.2 Khách đặt trước (`reservations`)

- Mỗi Ngày công bố R1,R2 sau `phase_start(gather)` theo ID, hiển thị trong HUD; Quán độc lập công bố lúc dựng pha. Hai bàn khác nhau, món theo day_plan (day) hoặc menu đầy đủ (quan), arrival_tick theo seed trong [1800,10799], có thể trùng tick.
- State `scheduled → holding → waiting → served|failed`. Bắt đầu giữ bàn từ `max(0, arrival_tick - 1800)`; khách đang ngồi có thể ở lại, khách mới không được ngồi bàn đã giữ. Lịch reservation trước khách thường.
- Đến giờ: nếu bàn bị chiếm → fail `occupied`; nếu thiếu stock → fail `stock`. Nếu tới được, giữ nguyên liệu ngay, phát `reservation_arrived` rồi `customer_arrived`, kiên nhẫn 60 s.
- Giá cuối `floor(freshness_base_price × 1.5)` trước khi tính boa. Thành công `served` rồi `reservation_served`.
- Fail do `stock`, `occupied`, `burnt`, `patience`, `closing`: trả phần giữ, dọn món, nhả bàn, reputation -1 **một lần**; dùng `reservation_failed`, không xử lý như khách thường. Spoiled re-reserve không đủ → fail stock. Khi burn: `dish_burnt` trước `reservation_failed`. Đóng ca fail mọi reservation chưa served/failed theo ID.
- Manifest `reservations {count:2,table_hold_s:30,price_multiplier:1.5,failed_reputation_delta:-1}`; scenario `quan.reservations[]` tối đa 2, table khác nhau, `arrival_tick` dương < thời lượng chuẩn, `quan.random_reservations:false` tắt sinh.
- Snapshot thêm reservations[], customers[].reservation_id, tables[].reservation_id (null nếu không có). Events `reservation_announced`, `reservation_arrived`, `reservation_served`, `reservation_failed` theo TICKET-03.

**Nhóm 5 người chỉ cần ít nhất một extension trong toàn lab**, không buộc chọn extension Phase 3. Nếu bật, ghi code extension ở manifest `extensions`, test và bằng chứng trong README. Khi tắt không thay đổi core.

## 12. Cách báo cáo hoàn thành (AI & thành viên)

Bất kỳ thành viên/Codex hoàn thành task P3-xx phải ghi:

1. **Source files changed:** phân biệt file sửa trực tiếp/file dependency.
2. **AC mapping:** các mục liên quan `P3-Txx`/yêu cầu chính thức, trạng thái PASS/PARTIAL/FAIL.
3. **Tests executed:** lệnh, thời điểm, số lượng pass/fail thực tế, fixture và commit hash.
4. **Integration:** API/schema đã chốt, thay đổi vào field dùng chung, rủi ro khi merge.
5. **Open issues:** việc chưa làm, phần chờ teammate, hướng xử lý tối thiểu.
6. **Git:** branch, status, commit gợi ý; không tự khai PASS cho test chưa chạy.

Khuyến nghị đặt `docs/notes/P3-01.md` … `P3-05.md`, làm verification chung tại `docs/verification/phase-3.md`, log thật trong `docs/proof/phase-3/`, ghi breaking change vào `CHANGELOG.md`.
