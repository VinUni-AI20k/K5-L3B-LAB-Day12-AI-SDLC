# Bàn giao Phase 1 — Lát 2

Mã và test được kiểm ở commit `4073fbf` trên nhánh `p1/gather-resources`. QA lead có thể dùng các kết quả dưới đây để điền ma trận Phase 1.

| Mục | Kết quả | Bằng chứng |
|---|---|---|
| Hái, bắt, mọc lại (PRD F) | Đạt ở cấp module. Sáu test kiểm mép bán kính, hòa theo ID, mọc lại và hái cùng bước, đầy giỏ và hồi bắt. Test dùng fixture giỏ theo giao diện lát 1. | [Log test](tests.log) |
| Trao đổi file kho (PRD G) | Đạt với fixture giỏ có sẵn. `gather_end` và file kho giống nhau, Quán nạp đúng ở tick 0. Hai lượt chạy cùng đầu vào giống nhau từng byte. Dừng do giới hạn tick giữ file cũ và không tạo file mới. | [Log smoke](smoke.log) · [Gather JSONL](gather.jsonl.txt) · [File kho](catch.json) · [Quán JSONL](quan.jsonl.txt) |
| HUD Gather | Chrome kiểm giờ, oxy, máu và giỏ `3/12`. Phím `E` cập bến, `R` khôi phục lượt chơi. | [Ảnh Gather](gather-hud.png) · [Log trình duyệt](browser.log) |
| HUD Quán | Chrome kiểm món gọi, kiên nhẫn, bếp, tay, tiền, uy tín và điểm. Có ba bông súng vật lý, khách giữ hai, HUD hiển thị một. Các nhãn chính cũng hiện ở chiều rộng 360 px. | [Fixture Quán](quan-hud.json) · [Ảnh Quán](quan-hud.png) · [Log trình duyệt](browser.log) |

## Chạy lại từ gốc repo

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```

```bash
proof=docs/proof/phase-1/nguoi-2
work=$(mktemp -d)
python3 -m chonoi.headless --mode gather --seed 42 --scenario "$proof/dock.json" --inputs "$proof/dock-inputs.json" --ticks 1 --out "$work/gather.jsonl" --inventory-out "$work/catch.json"
python3 -m chonoi.headless --mode quan --seed 42 --inventory "$work/catch.json" --ticks 0 --out "$work/quan.jsonl"
cmp "$work/gather.jsonl" "$proof/gather.jsonl.txt"
cmp "$work/catch.json" "$proof/catch.json"
cmp "$work/quan.jsonl" "$proof/quan.jsonl.txt"
```

Mở địa chỉ được in trong từng terminal để kiểm HUD với fixture.

```bash
python3 -m chonoi.live --mode gather --port 8000 --scenario docs/proof/phase-1/nguoi-2/dock.json
python3 -m chonoi.live --mode quan --port 8001 --scenario docs/proof/phase-1/nguoi-2/quan-hud.json
```

## Điểm bàn giao

- **Người 1** nối `tick_resources` sau khi giảm giờ, thay vòng giảm hồi cũ. Gọi `harvest` khi có cạnh `interact` và ở ngoài bến, rồi `catch_fish` khi có cạnh `catch`. Cả hai dùng `_try_add_to_hold` do lát 1 cung cấp.
- **QA lead** chạy lại chuỗi hái hoặc bắt → `gather_end` → Quán đọc kho. Kiểm thêm hành động ở tick hết giờ, bến đúng mép và ngất ghi kho rỗng trên bản đã nối. Sau khi có luật lát 3 và 4, chơi thử chuỗi nấu, lấy món, phục vụ và thu tiền.
- **Integrator** đối chiếu bằng chứng trên commit bàn giao và chốt tag. Lần kiểm này diễn ra trên nhánh lát 2.
- **Nhật ký AI** — Codex triển khai module tài nguyên, HUD, test và kiểm bằng Chrome. Token và chi phí chưa đo.
