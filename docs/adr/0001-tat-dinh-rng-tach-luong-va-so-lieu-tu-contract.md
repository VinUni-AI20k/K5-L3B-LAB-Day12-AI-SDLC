# ADR-0001: Tất định bằng RNG tách luồng và số liệu chỉ đọc từ contract

- Trạng thái: chấp nhận (quy tắc đã áp dụng từ Phase 1; ADR này ghi lại sau, sau Release `v1.0.0`)
- Ngày, người quyết: quy tắc của cả nhóm Nhom001 (xem `AGENTS.md`, mục "Cấu trúc & quy ước"); ghi ADR 2026-11-21, Nhat Minh

## Bối cảnh
- Test Contract đòi headless **tất định byte**: cùng `--seed`, cùng inputs → cùng file JSONL
  (`test_smoke_p2.test_ac_p2_91_day_one_full_loop_and_deterministic`, `test_gather_p2.test_ac_p2_09_spawn_deterministic_per_seed`,
  `test_quan_p1.test_ac_p1_24_arrival_choice_is_seeded_and_deterministic`, `test_p4_soak.test_deterministic`).
- Giảng viên chấm bằng fixture và có thể đổi `tuning` trong `game.contract.json`; luật hard-code số sẽ lệch khỏi contract.
- Ba người làm song song gather / quan / client; thêm một tính năng ngẫu nhiên ở module này không được làm lệch chuỗi
  ngẫu nhiên của module khác, nếu không test của người khác đỏ mà không ai sửa gì ở đó.

## Các lựa chọn đã cân nhắc
1. **Một `random.Random(seed)` dùng chung.** Đơn giản, nhưng mọi lần gọi thêm (ví dụ thêm khách đặc biệt ở quán)
   dịch chuỗi của mọi lần gọi sau → JSONL vàng của module khác đổi.
2. **`random` toàn cục / đồng hồ hệ thống.** Không tất định; loại ngay.
3. **Tách luồng theo mục đích (chọn).** `Streams(seed).get(name)` tạo `random.Random(f"{seed}:{name}")`, seed ổn định theo
   (seed, tên luồng), không phụ thuộc thứ tự gọi.

Về số liệu: (a) hằng số trong code luật, (b) **đọc từ `game.contract.json` → `tuning`** (chọn), kể cả ở client.

## Quyết định
- Mọi số ngẫu nhiên trong luật đi qua `Streams` (`chonoi/rng.py`). Luồng hiện có: `fish_spawn`, `fish_turn`
  (`chonoi/sim/gather.py`), `customers` (`chonoi/sim/quan.py`). Thêm tính năng ngẫu nhiên → thêm **luồng mới**, không mượn luồng cũ.
- Không dùng `random` toàn cục, không đọc đồng hồ hệ thống trong luật; duyệt thực thể bằng `ids.sort_by_id`, cấp id bằng `IdAllocator`.
- Số liệu luật (thời gian, giá, sức chứa, cấp nâng cấp…) chỉ đọc từ `tuning` của contract; `chonoi/contract.py` kiểm khoảng hợp lệ
  và trả mã 2 khi sai. Client đọc cùng file (`client/src/main.js`, `menu.js`, `deep.js` đọc `../game.contract.json`).
- Phần sáng tạo chỉ ở `client/` và tắt ở headless, nên không chạm luồng RNG hay JSONL.

## Hệ quả (module, file, test bị ảnh hưởng)
| Phạm vi | Hệ quả |
|---|---|
| `chonoi/sim/gather.py`, `chonoi/sim/quan.py` | Lấy RNG qua `streams.get(<luồng>)`; tham số đọc từ `tuning`. |
| `chonoi/contract.py` | Là nơi duy nhất kiểm khoảng giá trị `tuning`; thêm khóa → thêm kiểm ở đây. |
| `client/` | Đổi **kiểu** một khóa contract (ví dụ `fish_initial` mảng → số) phải sửa cả client. |
| `docs/contracts/`, `game.contract.json` | Đổi khóa hoặc `contract_version` → báo cả nhóm, cập nhật `CHANGELOG.md` và `docs/verification/phase-n.md`. |
| Test | Các test tất định ở trên là chốt chặn; thêm luồng mới không được làm đổi JSONL vàng của luồng cũ. |
| Đánh đổi | Tên luồng là một phần của hợp đồng ngầm: **đổi tên luồng = đổi chuỗi ngẫu nhiên**, phải coi như đổi hành vi. |
