# Báo cáo và bàn giao Gather Core — Thành viên 2

## Hiệu chỉnh theo PRD-0 — 2026-11-21

Tôi tạo nhánh `fix/ducbaynao-gather-prd-payloads` từ `6103c8f`, sau khi nhóm đã tích hợp Gather Items và quán. Các thay đổi của lần sửa này chưa được commit, push hoặc merge. Tôi giữ phạm vi TV2 theo phân công.

Tôi sửa `oxygen_empty` thành `{"oxygen_ticks":0}` và `faint` thành `{"cause":"choke","lost":[...],"hp":0}` theo PRD-0 E. Tôi lấy bản đảo của giỏ trước khi xóa, giữ đúng LIFO kể cả nguyên liệu trùng nhau. `gather_end` và dòng end vẫn dùng reason `fainted`, với kho rỗng.

Tôi đổi `_store_in_hold(kind, count)` sang nhận đủ lô hoặc trả 0 và giữ nguyên giỏ khi thiếu chỗ. Ví dụ còn một ô mà yêu cầu ba cá thì nhận 0. Hai đường hái/bắt của TV3 dùng helper sau kiểm tra sức chứa; hành vi `hold_full`, giữ đàn và cooldown được giữ nguyên. Tôi không sửa tuning, schema kho hay luật quán. Lý do sửa hợp đồng và kỳ vọng test nằm trong [ADR 0001](../../../adr/0001-gather-prd-payloads.md).

| Kiểm chứng mới | Kết quả | Bằng chứng hiện hành |
|---|---|---|
| Toàn suite sau tích hợp | 70/70 test qua, gồm 2 test CLI mới có subtest giỏ rỗng/trùng nguyên liệu | [Log mới](prd-correction/checks.txt) |
| Payload oxy/ngất | `oxygen_ticks:0`; ngất có đủ `cause/lost/hp`; `lost` đúng LIFO | [Chu trình oxy](prd-correction/oxygen-cycle.jsonl), [phiên ngất](prd-correction/faint.jsonl) |
| Giỏ và kho | Không nhận một phần yield; ngất ghi đè kho cũ bằng kho rỗng; cập bến giữ đúng hàng | [Log](prd-correction/checks.txt), [kho ngất](prd-correction/faint.inventory.json), [kho bến](prd-correction/dock.inventory.json) |
| Hồi quy/tất định | Gather và quan 600 ticks thoát 0; hai lần chạy ngất giống từng byte | [Hash và payload](prd-correction/summary.json) |
| Hồ sơ nhóm | Chưa đạt: thành viên 6 còn placeholder, TV3–5 đã có thông tin | [Kết quả TEAM thực chạy](prd-correction/summary.json) |

Tôi đã xác nhận ba test unit sửa theo PRD thất bại trên code cũ trước khi sửa code. Test CLI mới kiểm tra JSONL thực xuất, thứ tự event, giỏ rỗng, nguyên liệu trùng nhau và kho rỗng sau ngất. Tôi chỉ kết luận về Gather Core và hồi quy suite hiện có; chưa xác nhận toàn bộ DoD hoặc tag của nhóm.

Để tái chạy từ gốc repo: `python docs/proof/phase-1/member-2/verify.py` (Linux/macOS có thể dùng `python3`). Script tạo launcher Windows tạm, kiểm fixture và lưu kết quả mới vào `prd-correction/`; kiểm tra TEAM theo kết quả thực tế, không cố định thất bại. Nếu TEAM chưa đạt, đây vẫn là hạng mục chưa hoàn thành.

Tôi bàn giao [hợp đồng Gather](../../../contracts/README.md), [clarify 3/4/7](../../../clarify.md) và [ma trận kiểm chứng](../../../verification/phase-1.md) để Integrator review trên nhánh sửa lỗi. Ba commit ban đầu là `9b884d2`, `1fb7fbe`, `486d596`; lần hiệu chỉnh không viết lại lịch sử đã tích hợp.

## Lưu trữ — báo cáo lần bàn giao trước

Phần bên dưới và các log/JSONL/hash ở thư mục cha ghi lại thời điểm bàn giao ban đầu, còn payload cũ. Tôi giữ để truy vết; dùng `prd-correction/` ở trên khi đánh giá bản hiệu chỉnh. Số test, trạng thái tích hợp và TEAM trong bản lưu không còn đại diện cho repo hiện tại.

Tôi là **Phạm Lý Ngọc Đức (`Ducbaynao`)**, phụ trách lát 1 của `sim/gather`. Tôi thực hiện phần tương ứng commit 4–6 trong phân công, dựa trên trạng thái repo sau commit `533de26` của thành viên 1.

## Kết quả triển khai

Tôi so sánh phân vùng trước và sau di chuyển để phát `dive` hoặc `surface`, kèm bản sao vị trí tại thời điểm phát. Độ sâu bằng `surface_depth` vẫn thuộc mặt nước. Tôi tính oxy theo vị trí cuối bước: dưới nước trừ một tick, mặt nước hồi theo tuning và không vượt mức tối đa. `oxygen_empty` chỉ phát khi oxy từ dương giảm về 0.

Tôi bắt đầu đếm ngạt ngay trong tick oxy về 0. Mỗi `choke_interval_ticks` mất một máu và bộ đếm trở về 0; khi lên mặt nước, bộ đếm ngạt được xóa. Khi máu hết, tôi xóa giỏ trước khi phát `faint` rồi `gather_end(reason="fainted")`, và dừng xử lý tick trước các tương tác hoặc hết giờ. Runner hiện có ghi được kho rỗng mà không cần sửa khung.

Tôi giữ giỏ dưới dạng danh sách theo thứ tự nhặt, món mới nhất ở cuối. Hàm `_store_in_hold(kind, count)` nhận số lượng cần thêm và trả số lượng thực nhận trong giới hạn `hold_capacity`. Snapshot sao chép `hold`, `player.pos` và `player.vel` để giá trị đã đọc không đổi khi sim bước tiếp. Tôi sử dụng tuning hiện có, không sửa contract, schema kho, runner hoặc luật quán.

## Kiểm chứng đã thực hiện

| Hạng mục | Kết quả | Bằng chứng |
|---|---|---|
| Toàn bộ suite | 45/45 test qua, trong đó có 13 test Gather Core mới | [Log cuối](commit-6-checks.txt) |
| Unit module theo yêu cầu commit 6 | 20/20 test qua | [Log cuối](commit-6-checks.txt) |
| Chuyển vùng, cạn oxy và hồi oxy | `dive` tick 1, `oxygen_empty` tick 3, `surface` tick 10 | [Fixture](oxygen-cycle.scenario.json), [inputs](oxygen-cycle.inputs.json), [JSONL](oxygen-cycle.jsonl) |
| Ngạt và ngất | Choke tick 60/120/180, ngất và kết thúc tại tick 180; giỏ và kho rỗng | [Fixture](faint.scenario.json), [JSONL](faint.jsonl), [kho](faint.inventory.json) |
| Hồi quy cập bến | Kết thúc tick 1, giữ 1 cá lóc và 2 bông súng | [JSONL](dock.jsonl), [kho](dock.inventory.json) |
| Tính tất định | Hai lần chạy cùng seed/fixture ngất giống từng byte | [Mã kiểm chứng](verify.py), [SHA-256](summary.json) |
| Headless 600 ticks | Cả gather và quan thoát 0; kết thúc do giới hạn CLI, chưa hết phiên | [Gather](gather_run.jsonl), [quán](quan_run.jsonl) |
| Danh sách nhóm | Chưa đạt do TV3–6 còn placeholder | [Log cuối](commit-6-checks.txt) |

Tôi không xem việc CLI quán chạy được là bằng chứng nghiệp vụ quán đã hoàn thành. Tôi cũng chưa xác nhận phần hái/bắt cá của lượt TV3.

## Cách tái chạy

Từ thư mục gốc repo, trên máy Windows này:

```powershell
$env:PYTHONUTF8 = '1'
python docs/proof/phase-1/member-2/verify.py
```

Trên máy có Python dưới tên `python3`, dùng `python3` thay cho `python` ở lệnh trên. Script kiểm tra fixture qua bộ nạp scenario, chạy test và headless, so sánh byte rồi tạo lại các log/kho/hash trong thư mục này. Trên Windows, script tạo launcher `python3.exe` tạm cho lệnh trong contract và tự dọn khi xong; không cần sửa cấu hình hệ thống. Lần chạy được ghi nhận trong hồ sơ này dự kiến `check_team.py` trả 1 do TV3–6 chưa điền; sau khi hoàn thiện TEAM.md cần cập nhật kỳ vọng đó trong script.

## Bàn giao cho thành viên 3

- Tôi đã để nguyên TODO lát 2 trong `gather.py`. Tiếp tục xử lý hái bông, bắt cá và sự kiện `gather`/`fish_caught`/`hold_full` ở đúng vị trí sau cập nhật oxy/ngạt.
- Khi thêm đồ, gọi `_store_in_hold(kind, count)`; ví dụ còn một chỗ thì yêu cầu ba món trả về một. Hàm chỉ quản lý sức chứa, không tự phát event hay xóa đàn cá. TV3 cần quyết định hành vi thu hoạch theo yêu cầu đã chốt trước khi tích hợp.
- Tôi giữ nguyên thứ tự cập bến trước hái; ngất có ưu tiên trước cả hai. Không sắp xếp `hold`, vì sẽ mất thứ tự nhặt.
- Tôi bàn giao [ma trận kiểm chứng](../../../verification/phase-1.md), [fixture và hash](summary.json). Sau khi tích hợp lát 2 cần chạy lại test và tạo bằng chứng mới trước tag `phase-1`.

## Ba commit phần việc của tôi

1. `9b884d2` — `feat(gather): implement surface transitions and oxygen consumption` — [36 test và smoke](commit-4-checks.txt).
2. `1fb7fbe` — `feat(gather): implement choking damage and fainted state` — [41 test và smoke](commit-5-checks.txt).
3. `feat(gather): integrate LIFO hold storage and synchronize snapshot fields` — giỏ/snapshot, 13 test Gather Core và hồ sơ này — [45 test và smoke](commit-6-checks.txt).

Tôi tra mã commit thứ ba bằng `git log -1 --oneline` tại thời điểm bàn giao. Ba commit được lưu cục bộ; tôi chưa đẩy nhánh hoặc gắn tag thay phần việc của người tiếp theo.
