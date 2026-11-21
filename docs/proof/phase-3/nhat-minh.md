# Nhật Minh — Phase 3: độ tươi và dòng nước

Ticket **02 freshness** và **07 current**. Nguồn: spec P3, ticket nhóm và ADR-0001.
Mã luật đã cài trên `feat/nhat-minh`; **chưa xác nhận tích hợp toàn bộ v1.2**.
Adapter `Stock`, migration kho và vòng day/shop do owner khác phụ trách, chưa có API/commit v1.2 để ghép.

## Độ tươi

- `freshness.py`: giữ `fresh_units` nguyên, 240 units/điểm; preset hao 2 units/tick.
  Rate khác đọc từ dữ liệu, dùng phần dư hữu tỉ để không trôi sai số hoặc làm tròn rate mỗi tick.
- Hàng có sẵn hao ở đầu bước; hàng mới thêm sau đó giữ 100 trong bước nhận. Vượt từ >=30 xuống <30
  phát `spoiled` một lần theo numeric ID. Hàng ươn vẫn chiếm ô; fresh kẹp đáy 0.
- Hái/bắt tạo ID `I` bằng `IdAllocator`, event có `item_ids`; fixture được reserve trước khi cấp ID mới.
  Dùng lại allocator thì ID tiếp tục xuyên pha/Ngày. Net tạo ID cho từng đơn vị nhận được.
- Snapshot giỏ giữ thứ tự nhặt. Payload handoff sắp ID; payload mất hàng LIFO xuất `{id, kind, fresh}`.
  Giỏ ngất rỗng xuất `{"items":[]}` ở event, chưa khẳng định writer kho của nhóm đã hỗ trợ schema này.
- Helper Cá Sấu giữ nguyên từ `6187354`; gather đổi payload lost sang dạng xuất sau khi áp dụng luật.

## Dòng nước

- `current.py` đọc interval/duration/warning/min_depth/speed từ tuning; chỉ tạo khi có extension `current`.
- Preset cảnh báo tick 1680, bắt đầu tick 1800 trước di chuyển, hết ở tick 2280 trước di chuyển.
  Snapshot đầu có 480 tick, tick cuối có 1. Hướng qua `Streams("current")` hoặc khóa bằng scenario.
- Chỉ cộng dịch chuyển ngang theo độ sâu **đầu bước**, không tích vào `player.vel`; chặn biên bình thường.
  Cá/quái không bị đẩy. `random_current:false` tắt lịch.
- Kết thúc pha đóng current đúng một lần; `current_end(phase_end)` đứng trước `faint`/`gather_end`,
  kể cả khi helper Cá Sấu tự gọi `_finish`. Không phát thêm event bắt đầu ngoài ticket.
- Không bật extension: không RNG/event/field current mới, cùng byte với lõi.

## Kiểm chứng và giới hạn

```powershell
$env:PYTHONPATH = 'tests;.'
python3 -m unittest discover -s tests -p test_gather_extensions.py -v
python3 tools/check_nhat_minh.py --with-integration-patches --out docs/proof/phase-2/with-proposed-hooks.txt
```

30 ca component trong `test_gather_extensions.py` kiểm net/fresh/current, ngưỡng 30, spoiled theo ID,
hao/chặn 0, LIFO do ngạt và Cá Sấu, net + cá thể, ID xuyên pha, freeze khi caller không step, force/biên,
lịch hiện hành/kết thúc pha, tắt extension và tất định. Probe chạy ở subprocess qua
`GatherSim.from_contract`; **dữ liệu đã chuẩn hóa**, không chạy qua validator schema/file kho v1.2.
Probe xuất JSONL ngay mỗi bước để không giữ tham chiếu snapshot thay đổi theo bước sau.

Lịch current và lực đẩy được kiểm thêm qua **headless thật** trong `test_net_day_rules.py`, với metadata hooks
chỉ ghép ở thư mục tạm. Ca này dùng contract đếm v1.1 và dữ liệu oxygen lớn hơn để sống đủ 2280 tick;
không dùng ca này làm bằng chứng migration v1.2.
[Log chung](../phase-2/with-proposed-hooks.txt), [log bản làm việc](../phase-2/local-all-tests.txt).
Kết quả cuối: **174/174 qua** trên dependency v1.1 với các patch bàn giao trong thư mục tạm;
bản làm việc contract v1.0 **104 test qua, 2 class báo skip** do thiếu data/hook P2.
Thêm [6 ca kiểm patch scenario](current-schema-proposal.txt) qua CLI: khóa hướng ±1,
random_current:false và từ chối hướng 0/bool, random_current sai kiểu trước khi tạo output.
Patch schema cũng chỉ ghép trong thư mục tạm.

## Việc cần owner ghép

1. Ticket 01 của Cao Minh: `Stock`/validator/reader/writer v1.2; xác nhận API add/take/items cụ thể.
   Gather hiện có phần luật và xuất/nhận mảng cá thể tại biên chuẩn hóa, **chưa chuyển sang gọi lớp Stock**.
   Đây là điểm tích hợp còn lại theo ADR, không đánh dấu đáp ứng điều kiện bật v1.2.
2. Ghép dữ liệu theo [fragment manifest](integrator-manifest-fragments.json), bổ sung kiểm dải giá trị,
   schema `hold`; [patch scenario current](integrator-current-scenario.patch) đã chuẩn bị để owner nhận
   `random_current` và `current_direction` trong validator. Patch chưa áp dụng vào source framework.
3. Dùng factory manifest hoặc [metadata hooks](../phase-2/integrator-extension-hooks.patch);
   runner/day giữ allocator qua pha/Ngày, giữ nguyên tuổi khi bàn giao và không gọi step khi pause.
4. QA chạy migration hai schema, gather → file → quan, giữ chỗ/giá theo tươi và day đầy đủ sau khi adapter/quán xong.

Không sửa `inventory.py`, `contract.py`, `scenario.py`, `runner.py`, bootstrap hoặc contract gốc.
Không Git merge/commit/push/tag; chưa có người review các thay đổi mới.
