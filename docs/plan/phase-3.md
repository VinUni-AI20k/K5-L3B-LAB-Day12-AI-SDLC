# Kế hoạch Phase 3 Phoenix

Mốc bắt đầu là tag `phase-2` tại `5455042`. Ticket-03 yêu cầu theo dõi độ tươi từng nguyên liệu xuyên Gather, Quán và vòng `day`. Phạm vi là lõi Test Contract v1.2. [Hợp đồng kho cá thể](../contracts/phase-3.md) và [ADR đổi schema](../adr/0001-inventory-items.md) chờ Khôi review trước khi dùng để bàn giao.

## Phân công và tiêu chí chấp nhận

| Người | Phạm vi sở hữu | Điều kiện bàn giao |
|---|---|---|
| Diên · `dinhphucdien179` | AC-P3-01–02. Adapter/mô hình cá thể, giỏ Gather, hao tươi và event/LIFO. | Test chung cho schema kho cũ và mới. Test bắt/hái cấp ID, hao đúng tick, ươn, rơi cá thể và xuất kho. |
| Nhân · `ying684` | AC-P3-03–04. Kho Quán, giữ theo ID, cấp lại khi ươn, giá, boa và fixture đơn. | Test nhiều đơn giữ riêng, kho đang giữ vẫn hao, cấp lại đủ/thiếu, ghi giá đã chốt và thanh toán. |
| Khôi · `KN-16` | AC-P3-05–06. Nối adapter vào CLI, scenario, Day/Shop và JSONL, HUD độ tươi, manifest, bằng chứng và tag. | Smoke file lẫn `day`, kiểm lần lượt v1.1 và v1.2, hồi quy còn hiệu lực, CHANGELOG, ma trận và log thực tế. |

### Diên · PR thứ nhất · `phoenix/p3-gather` → `main`

Giữ `chonoi/freshness.py`, `chonoi/inventory.py`, `chonoi/sim/gather.py` và test của phần này. Tách hai nội dung commit.

1. **AC-P3-01 · Adapter và mô hình cá thể.** Tạo helper theo hợp đồng, kiểm schema, đọc/ghi theo version, ghi nguyên tử và sắp ID ổn định. Có test đối chiếu hai file mẫu. Ở v1.2 nhận hàng đã ươn, từ chối kho đếm, ID trùng, loại lạ và độ tươi sai. Kiểm xuất rồi đọc lại quanh ngưỡng 30.
2. **AC-P3-02 · Giỏ Gather.** Kích hoạt nhánh mới theo tuning `freshness`. Dùng allocator cấp ID theo lượt hái/bắt. Hao toàn bộ hàng có sẵn đầu tick trước di chuyển và tương tác. Hàng vừa lấy vẫn 100. Khi mất hàng, giữ LIFO. Về bến hoặc hết giờ bàn giao giỏ còn lại, ngất xuất `items: []`. Test `spoiled` đúng một lần tại tick qua ngưỡng, xử lý cùng tick theo ID, thứ tự rơi và giới hạn tick giữ file đích.

PR đầu bàn giao API và test v1.2 qua fixture, còn manifest trên `main` vẫn v1.1. Tag Phase 2 và test kho đếm tiếp tục chạy như trước. Gửi Nhân SHA sau khi PR gộp.

### Nhân · PR thứ hai · `phoenix/p3-quan` → `main`

Giữ `chonoi/sim/quan.py` và test Quán. Bắt đầu song song từ `phase-2` theo hợp đồng và fixture. Chạy test nối adapter sau khi PR Diên đã vào `main`. Tách hai nội dung commit.

1. **AC-P3-03 · Kho và giữ hàng.** Nhận kho cá thể, trừ phần giữ khỏi kho khả dụng, loại hàng ươn khỏi món có thể nấu. Giữ từng ID theo độ tươi giảm dần rồi ID tăng dần. Ở đầu tick, phát tất cả `spoiled` theo ID rồi xét các đơn bị ảnh hưởng theo `order_tick`, ID bàn. Mỗi đơn nhả toàn bộ và thử giữ lại một lần. Thiếu hàng chuyển `unfulfillable`. Test fixture giữ trùng, sai công thức, giữ hàng ươn, nhiều đơn cạnh tranh và nhả ID khi khách rời.
2. **AC-P3-04 · Nấu và chốt giá.** Tiêu đúng ID đã giữ lúc nấu. Chốt giá theo trung bình độ tươi ở tick nấu, tính boa từ giá đã chốt và giữ tiến trình giao/thu tiền của Phase 2. Đưa cá thể đã tiêu vào event `cook_started` đúng thứ tự. Test hòa độ tươi, phép floor, thiếu hàng ươn, giao sát hạn và đóng ca. Snapshot giữ cả hàng ươn, phần giữ chỉ chứa danh sách ID.

Sau khi Diên đã gộp, cập nhật nhánh Quán từ `main`, chạy test lát và regression rồi mới gộp PR. Manifest vẫn v1.1 ở lần gộp này. Gửi Khôi SHA sau khi Quán gộp.

### Khôi · PR thứ ba · `phoenix/p3-integration` → `main`

Giữ manifest, `scenario.py`, `headless.py`, `live.py`, `runner.py`, `day.py`, `jsonl.py`, `web/index.html` và tài liệu bàn giao. Không sửa luật trong hai lát trừ điều chỉnh tích hợp cần thiết. Khôi chốt giao diện, review bằng chứng và làm các lệnh remote.

1. **AC-P3-05 · Kết nối và HUD.** Nối version vào đọc/ghi kho và kiểm scenario. Bật v1.2 trong PR cuối. Giữ độ tươi và ID tại tick chuyển pha. Ngày đầu giữ ID của fixture, Ngày sau cấp lại theo thứ tự từ cùng allocator. Shop giữ mảng kho dư và không hao tươi. UI đọc được giỏ, kho khả dụng, độ tươi và nhãn ươn. Các bộ đếm kế hoạch Ngày vẫn dùng tổng theo loại.
2. **AC-P3-06 · Kiểm và bàn giao.** Smoke file qua hai tiến trình, smoke `day`, kiểm pause, kiểm kho đếm trả mã 2 và hồi quy P1–P2 còn hiệu lực. Ghi breaking change vào `CHANGELOG.md`, ma trận trong `docs/verification/phase-3.md`, log trong `docs/proof/phase-3/`, cập nhật clarify, nhật ký AI và retro. Gắn `phase-3` từ commit đã kiểm trên `main` sau khi PR cuối gộp.

## Thứ tự PR và quy tắc Git

**Diên → Nhân → Khôi.** Mỗi người mở một PR triển khai vào `main`. Có thể làm song song. Khôi đưa tài liệu kickoff và fixture mẫu lên `main` trước để cả nhóm cùng pull. Diên mở PR code đầu tiên.

- Bắt đầu bằng `git switch main` rồi `git pull --ff-only origin main`. Tạo nhánh cá nhân bằng `git switch -c <nhánh>`. Nếu nhánh đã tạo, chuyển sang nhánh đó.
- Nhân đồng bộ sau khi Diên gộp. Khôi đồng bộ sau khi cả hai đã gộp. Nếu commit còn ở local, có thể rebase nhánh cá nhân lên `main`. Nếu nhánh đã push và có người dùng, gộp `main` vào nhánh để giữ lịch sử.
- Trước khi đẩy, test lát riêng và chạy test chung. Stage từng file đã review. Đặt output thử tay và kit trong `tmp/`, giữ `.gitignore`, `.venv` và `.env` ngoài staging. Khi làm chung commit, điền `Co-authored-by:` cho người thực sự cùng làm.
- Chọn **Create a merge commit** để giữ commit tác giả. Nhân hiện có 2 commit nội dung trong cả lab, nên commit Phase 3 cần có phần Quán đã làm và kiểm thử thực tế.
- Khi sẵn giai đoạn tích hợp, smoke kho ở điểm kiểm phút 20 của đợt build. Nếu thiếu commit phụ thuộc, ghi SHA đang chờ rồi dừng phần phụ thuộc.

## Giao một task cho AI agent

```text
Tôi là <Diên/Nhân/Khôi>, làm <AC-P3-xx> trên <nhánh>.
Đọc Ticket-03, AGENTS.md, phần tôi trong kế hoạch Phase 3 và hợp đồng kho cá thể.
Chỉ sửa các file thuộc lát của tôi. Giữ chế độ v1.1 hoạt động trước khi Khôi bật v1.2.
Dùng .venv, đặt file thử tay ở tmp/, chạy test lát và test còn hiệu lực.
Trả danh sách file, lệnh và kết quả thật, lỗi phát hiện và commit phụ thuộc nếu có.
Tôi đọc diff, xác nhận nội dung, commit và push bằng tài khoản của mình.
```
