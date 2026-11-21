# Hợp đồng tích hợp Phase 2

Mốc gốc là tag `phase-1` tại `ad79355`. [Dữ liệu Phase 2](phase-2.tuning.json) ghi các giá trị thêm hoặc thay đổi. Manifest v1.1 kết hợp dữ liệu này với ba món P1 và các hằng số giữ nguyên theo Ticket-02. PR cuối của Khôi bật v1.1 sau khi cả Gather và Quán đã vào nền `main`.

## Giao diện giữa các lát

| Thành phần | Giao diện |
|---|---|
| Gather | `GatherSim(tuning, scenario, streams, ids, *, day=1)`. Dùng `day` để chọn quái mặc định. Runner truyền tuning gather với giới hạn oxy và Máu theo cấp đang áp dụng. Đầu ra bàn giao vẫn là `inventory_items()` dạng map đếm từ giỏ, khớp `gather_end.data.inventory.items`. |
| Quán | `QuanSim(tuning, scenario, streams, ids, inventory=None, *, day_plan=None, progress=None)`. `day_plan` có `dishes` và `ingredients`. Khi có kế hoạch, chỉ chọn món trong `dishes` đủ nguyên liệu. Với `None`, dùng toàn bộ menu. `progress` chứa `money`, `earned`, `reputation` khi vào Quán trong `day`. Quán trả tổng tại cuối ca và giữ `shift_earned` riêng. |
| Runner | Sở hữu ngày, chuyển pha, kho bàn giao và trạng thái tài chính xuyên ngày. Dùng chung `Session` cho headless và live. Snapshot `day` có `day`, `day_plan`, `upgrades`, `active_upgrades`. UI đọc snapshot và gửi lệnh, chạy màn giới thiệu/tổng kết bên ngoài tick gameplay. |
| Adapter | Khôi sửa validator, scenario và inventory dùng chung. `day` nhận khối `day`, `gather`, `quan` làm mẫu. Trong `day`, `quan.stock` và `quan.reputation` là đầu vào sai. Kiểm các ràng buộc phụ thuộc kho thật khi dựng ca Quán. Kho đếm thêm `ca_keo` và `keo_neo`. |

## Luồng ngày và bộ đếm

- `--days` chỉ dùng với `--mode day` và nhận 1–5, mặc định 1. `--inventory-out` dùng cho gather độc lập, `--inventory` dùng cho quán độc lập. Trong `day`, chuyển kho qua bộ nhớ. Ca ngất bàn giao kho rỗng.
- `day_start → day_plan → phase_start(gather)`. Cùng tick kết thúc phát sự kiện pha cũ trước rồi `phase_start` cho pha mới. Snapshot chuyển pha dùng `phase_tick: 0`. Gameplay pha mới bắt đầu bước sau. Event trong `day` có trường `day`.
- `tick` tính mọi bước đầu vào, `sim_tick` tính bước chạy luật, `phase_tick` tính bước trong pha. Xử lý cạnh `pause` trước. Tạm dừng giữ timer, lịch, chuyển động và Shop. Cạnh bỏ pause chạy luật ngay bước đó. Dùng cùng latch qua đổi pha cho `interact`, `catch`, `pause`, `shop_done`. Lệnh chuỗi `buy` chỉ có hiệu lực tại frame khai báo.
- Trong Shop, xử lý `buy` trước cạnh `shop_done`. Shop hết 600 tick hoạt động thì tự đóng. Tăng `days_completed` khi Shop đóng, kể cả ngày cuối. Cấp mua đổi ngay trong `upgrades`, chỉ sao vào `active_upgrades` khi bắt đầu Ngày kế tiếp. Giữ tổng tiền và uy tín, làm mới giỏ và bỏ kho dư sau Shop.

## Kiểm tích hợp

1. Chạy hai tiến trình gather → file kho → quan với seed 42. Kiểm kho ở tick 0 và thử cả hai nguyên liệu mới khi xác nhận v1.1.
2. Chạy `day --days 1` và nhiều ngày. Dùng fixture đầu kỳ có đúng 200 nghìn để mua cấp oxy đầu, kiểm tiền/thu nhập và oxy qua Ngày 2. Kiểm thứ tự event, lỗi fixture, pause trong mỗi pha và cả nhánh ngất.
3. Chạy các regression còn hiệu lực và ghi lý do khi đổi giả định P1 như số đàn cá, số bàn hoặc tập món. Không thay kết quả tại tag P1.
