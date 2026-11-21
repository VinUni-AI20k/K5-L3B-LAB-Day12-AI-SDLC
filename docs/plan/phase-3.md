# Kế hoạch Phase 3 — TICKET-03 "Mùa Nước Nổi" (Contract v1.2)

- **Khung giờ:** 35 phút (1:55–2:30). **Hạn:** tag `phase-3` trên commit bàn giao ở `main` trước 2:30.
- **Mục tiêu:** chuyển **kho đếm → kho cá thể** `{id,kind,fresh}` ở cả file kho, gather, quán và `day`. Có thêm hao tươi, hàng ươn (< 30), giữ chỗ theo id, giá theo độ tươi và HUD hiện độ tươi. Đây là **breaking change**: file kho đếm phải trả mã 2 khi chạy v1.2.
- Phân việc tổng thể và "nhà" của từng người xem ở [phan-chia-cong-viec.md](phan-chia-cong-viec.md) mục 0.

## 0. Hiện trạng trước Phase 3 (main `3ce5cc6`, PO ghi lúc pull)

| Hạng mục Phase 2 | Trạng thái | Ảnh hưởng tới Phase 3 |
|---|---|---|
| `contract_version` vẫn là `"1.0"`, chưa có số chuẩn v1.1 | ❌ chưa làm | v1.2 xây trên v1.1: cần `ca_keo`, `keo_neo`, 6 món, N5/N6 trước khi thêm khối `freshness` |
| `sim/day.py`, `--mode day`, Shop | ❌ chưa có | Không có `day` thì không làm được phần bàn giao trong cùng tick và id xuyên Ngày |
| `sim/monsters.py` (Cá Sấu, `monster_hit`) | ❌ chưa có | `lost` dạng mảng cá thể chỉ áp được cho `faint` do ngạt |
| Cá bơi/sinh (Dũng) | ✅ trên main | Giữ nguyên, chỉ đổi phần giỏ |
| 2 bếp, 6 món, `burn` (Kiên) | 🟡 ở nhánh `p2/quan-2bep-6mon`, chưa gộp | Gộp **trước** phút 7 để Quán v1.2 sửa trên một bản duy nhất |
| Nhánh `NguyenQuangDung` (4 commit) | 🟡 chưa gộp | Dũng mở PR hoặc xác nhận đã có trên main |

**Nguyên tắc:** Phase 3 không chờ Phase 2 xong hết. Lặn và Quán làm độ tươi ngay trên `GatherSim`/`QuanSim` hiện có. Phần `day` chỉ làm khi `sim/day.py` đã gộp. Nếu tới phút 25 vẫn chưa có `day`, ghi trung thực "chưa đạt" trong verification và không giả bằng chứng.

## 1. Phút 0–7: chốt quyết định (Integrator chốt, PO ghi `docs/adr/0002-kho-ca-the.md`)

1. **Biểu diễn độ tươi chính xác:** lưu `fresh` bằng `fractions.Fraction`, đọc từ JSON qua chuỗi thập phân để giữ đúng giá trị fixture như `97.5` hay `33.3`. Mỗi tick, gather trừ `Fraction(1,120)` (0.5/s) và quán trừ `Fraction(1,240)` (0.25/s), kẹp đáy 0. So ngưỡng `fresh < 30` và tính `floor` trên Fraction, chỉ đổi sang float khi ghi JSON. (Ticket gợi ý 240 đơn vị/điểm, nhưng cách đó chỉ đúng khi fixture là bội của 1/240. Fraction đúng với mọi đầu vào.)
2. **Một kiểu dùng chung** `Item(id, kind, fresh)` đặt trong `chonoi/inventory.py`. Gather, quán và day chỉ dùng kiểu này, không ai tự định nghĩa lại.
3. **Một bộ đếm id `I<n>`** dùng `IdAllocator`. Gather và quán độc lập: bộ đếm tiếp nối hậu tố lớn nhất đã nạp. `day`: DaySim giữ một bộ đếm xuyên pha và Ngày. Ngày 1 giữ nguyên id trong `gather.hold`, các Ngày sau cấp id mới theo thứ tự mảng.
4. **Chuyển an toàn:** adapter đọc theo `contract_version` (1.0/1.1 → kho đếm, 1.2 → kho cá thể). Chỉ lật `"1.2"` khi Lặn và Quán đã xong, để `main` luôn xanh.
5. **Thứ tự trong tick** (dán nguyên văn vào `docs/contracts/`):
   - Gather: đồng hồ, cooldown, hồi nút, **hao tươi hàng có sẵn đầu bước** → bơi/oxy/ngạt → quái/hit → bến trước hái → bắt cá → hết giờ → cá bơi/sinh. Hàng mới `fresh=100`, hao từ bước sau.
   - Quán: đồng hồ, timer → **hao tươi kho thô (gồm hàng đang giữ) → phát hết `spoiled` theo id → xử lý đơn có hàng vừa ươn** (theo `order_tick` rồi id bàn) → món chín/cháy theo id bếp → di chuyển và tối đa một tương tác → thanh toán, kiên nhẫn, đóng ca → khách mới.

## 2. Bảng tác động và chia việc

| Module | File | Việc cụ thể | Test thêm/đổi (chủ lát viết) | Người |
|---|---|---|---|---|
| Adapter + contract | `chonoi/inventory.py`, `game.contract.json`, `docs/contracts/` | `Item`, đọc/ghi 2 schema theo version, ghi nguyên tử, sắp theo id. Khối `freshness {initial:100, gather_decay_per_s:0.5, quan_decay_per_s:0.25, spoiled_below:30}`. Gộp luôn các khóa v1.1 còn thiếu (6 nguyên liệu, 6 món, N5/N6) | `tests/test_p3_inventory.py`: kho đếm khi v1.2 → mã 2; id trùng, id rỗng, kind lạ, fresh ngoài [0,100] → mã 2; ghi rồi đọc lại giữ đúng giá trị ở ngưỡng 30 | **invzble-z** |
| Scenario | `chonoi/scenario.py` | `gather.hold`, `quan.stock` thành mảng cá thể. `customers[].reserved` thành mảng id. Kiểm id vật lý duy nhất giữa giỏ, kho, phần giữ; phần giữ phải chưa ươn, đủ công thức, không dùng chung đơn. Thiếu `reserved` thì cấp tươi nhất rồi id nhỏ | `tests/test_p3_scenario.py`: các ca mâu thuẫn → mã 2 | **WorkOfMinh** |
| Lặn: giỏ, id, hao, ươn | `sim/gather.py` | Cấp id khi hái/bắt (đàn cá cấp nhiều id liên tiếp), hao 0.5/s, `spoiled {item_id,kind,location:"hold"}` đúng 1 lần, `gather_end.inventory` và `--inventory-out` theo schema mới | Ngưỡng: scenario mẫu của ticket `fresh:30` → `spoiled` ở tick 1. Id tăng theo thứ tự vào giỏ | **NguyenQuangDunghe161764** |
| Lặn: mất hàng | `sim/gather.py` (ngất), `sim/monsters.py` (nếu đã có) | `faint.lost` và `monster_hit.lost` là mảng cá thể theo LIFO. Nếu đang viết `monsters.py` (nợ P2) thì viết thẳng trên `Item` | `lost` là mảng cá thể LIFO khi ngất do ngạt (và do hit nếu có quái) | **comtrang378-ship-it** |
| Quán: kho, giữ chỗ | `sim/quan.py` (khách) | `stock` mảng cá thể, hao 0.25/s kể cả hàng giữ, `spoiled` location `stock`. Giữ theo id: mỗi loại lấy tươi nhất, hòa theo id. Hàng giữ vừa ươn → nhả toàn bộ phần giữ, giữ lại đúng 1 lần, thiếu → `unfulfillable`, khách chờ tới hạn | Hàng giữ vừa ươn → nhả, giữ lại 1 lần, thiếu → `unfulfillable`. Thứ tự xử lý nhiều đơn | **Quoosc** |
| Quán: nấu, giá | `sim/quan.py` (bếp, tiền) | Nấu tiêu đúng id đang giữ. `base_price = floor(giá × trung bình fresh / 100)`, boa `floor(base_price × 0.2)`. `cook_started.items` là mảng cá thể sắp theo kind rồi id. `burn` (đã làm ở P2): món cháy mất nguyên liệu, giữ lại theo luật mới | Giá theo tươi + boa trên giá đã chốt. Món chín không hao | **ttkien0710** |
| day | `sim/day.py` | Bàn giao kho trong cùng tick chuyển pha, không hao thêm, quán chạy từ bước sau. Bộ đếm id xuyên Ngày. Hàng ở Shop không hao | Bàn giao day giữ đúng id/kind/fresh | **invzble-z** (sau adapter, chỉ khi `day.py` đã có) |
| HUD độ tươi | `chonoi/web/` | Thanh hoặc số độ tươi cho từng cá thể trong giỏ (sáng) và kho (tối), nhãn/màu "ươn" khi < 30. Dùng mock snapshot có `fresh` để không chờ sim | `tests/test_live_static.py` còn xanh, ảnh chụp vào `docs/proof/phase-3/` | **nganhduong123** |
| QA + bằng chứng | `tests/`, `docs/proof/phase-3/`, `docs/verification/phase-3.md` | Smoke bàn giao file (ticket §1), smoke `day` nếu có, regression P1–P2, ma trận AC-P3-xx | Ghi lý do cho mọi test cũ đổi vì schema mới | **WorkOfMinh** |
| Ghi chép | `CHANGELOG.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md` | Bản nháp CHANGELOG (breaking change, schema mới, cách sửa fixture) để Integrator duyệt. Cập nhật clarify, nhật ký AI, retro về lần đổi kho | — | **nganhduong123** |

> Kiên và Quốc cùng sửa `sim/quan.py`: Quốc giữ các hàm khách/giữ chỗ, Kiên giữ bếp/tiền. Hàm chọn cá thể tươi nhất (`pick_freshest`) do Quốc viết, Kiên chỉ gọi.

## 3. Thứ tự tích hợp (giữ main xanh)

| Phút | Việc | Ai |
|---|---|---|
| 0–7 | Gộp `p2/quan-2bep-6mon` và nhánh của Dũng. Chốt mục 1, ghi ADR 0002 | invzble-z (gộp), nganhduong123 (ghi) |
| 7–12 | PR adapter: `Item`, đọc/ghi 2 schema, khối `freshness`, khóa v1.1 còn thiếu, **vẫn để `"1.1"`**. Các lát khác rebase ngay sau khi gộp | invzble-z |
| 7–12 | Viết test đỏ trước: ngưỡng, giữ lại, giá, mã 2 | Dũng, Quốc, Kiên, Minh |
| 12–25 | Song song: Lặn (Dũng, Tú), Quán (Quốc, Kiên), Scenario (Minh), HUD (Dương), `day` nếu có (Bào) | cả nhóm |
| 20 | **Smoke bàn giao file:** gather 1 bước với `{"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":100}],"random_fish":false,"monsters":[]}}` + `interact:true` ở frame 0 → `quan --inventory --ticks 0`, so chính xác id/kind/fresh. **Standup 2–3 phút** (PO ghi `docs/standup.md`), điều người xong sang lát trễ | WorkOfMinh, cả nhóm |
| 25 | **Lật `contract_version:"1.2"`**, cập nhật fixture cũ sang mảng cá thể | invzble-z |
| 25–32 | Smoke file + `day`, regression P1–P2, `docs/verification/phase-3.md`, `docs/proof/phase-3/`. Chốt CHANGELOG. Retro nhanh về lần đổi kho | Minh (QA), Bào (CHANGELOG), Dương (retro) |
| 32–35 | Dự phòng. **Bào gắn tag `phase-3` ≤ 2:30** | invzble-z |

Người xong sớm: Kiên → hỗ trợ `day` của Bào. Dũng → hỗ trợ Tú với `monsters.py` hoặc làm mở rộng `current`.

## 4. AC-P3 (QA giữ ma trận, chủ lát nộp bằng chứng)

| AC | Nội dung | Kiểm bằng | Người |
|---|---|---|---|
| AC-P3-01 | v1.2: file kho đếm, sai schema, kind lạ, id trùng, fresh ngoài miền → mã 2 | test đơn vị + headless | invzble-z |
| AC-P3-02 | Hàng mới `fresh=100`, hao 0.5/s ở giỏ, 0.25/s ở kho, kẹp 0, pause dừng hao, món chín không hao | test | Dũng, Quốc |
| AC-P3-03 | `spoiled` đúng 1 lần khi từ ≥ 30 xuống < 30, theo id, đúng `location` | scenario mẫu của ticket | Dũng, Quốc |
| AC-P3-04 | Giữ theo id tươi nhất. Hàng giữ vừa ươn → nhả, giữ lại 1 lần, thiếu → `unfulfillable` | test | Quoosc |
| AC-P3-05 | `base_price` theo trung bình fresh, boa trên giá đã chốt, `cook_started.items` đúng thứ tự | test | ttkien0710 |
| AC-P3-06 | `lost` trong `faint`/`monster_hit` là mảng cá thể LIFO | test | comtrang378-ship-it |
| AC-P3-07 | Bàn giao file giữ đúng id/kind/fresh (smoke ticket) | smoke 2 tiến trình | WorkOfMinh |
| AC-P3-08 | Bàn giao trong `day` cùng tick, id tăng xuyên Ngày | smoke `day --days 2` | invzble-z |
| AC-P3-09 | HUD cho thấy độ tươi hoặc hàng ươn | ảnh chụp live | nganhduong123 |
| AC-P3-10 | Regression P1–P2 còn hiệu lực đạt, test đổi có lý do. CHANGELOG có breaking change | chạy toàn bộ test | WorkOfMinh |

## 5. Mở rộng (chỉ khi lõi v1.2 xanh trước phút 25)
- Ưu tiên **chất lượng lõi** và trả nợ Phase 2 (`day.py`, `monsters.py`) hơn thêm mục mới.
- Nếu dư thời gian: `current` (Dòng nước lũ), NguyenQuangDunghe161764 làm (chỉ cộng 1.5 m/s vào player khi d ≥ 10, có lịch báo trước). `reservations` quá lớn cho 35 phút, **không làm**.
- `burn` của Kiên (từ P2) phải chạy đúng với kho cá thể thì mới tính là mở rộng.

## 6. Rủi ro
- **Đường găng là adapter (Bào), và Bào còn nợ `day.py`.** Scenario đã chuyển cho Minh, CHANGELOG nháp chuyển cho Dương để Bào bớt tải. Nếu adapter chưa gộp ở phút 12, Dũng và Quốc dùng tạm `Item` tự khai trong nhánh rồi đổi import khi gộp.
- Quốc và Kiên cùng sửa `sim/quan.py`: chia đúng hàm như bảng trên, rebase thường xuyên.
- Sai số làm tròn ở ngưỡng 30 và ở `floor` giá: chỉ dùng Fraction, không dùng float trong luật.
