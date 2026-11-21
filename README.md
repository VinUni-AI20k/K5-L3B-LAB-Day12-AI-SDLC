# Quán Ăn Chợ Nổi — nhóm 6667

Game 2D quản lý quán ăn miền Tây: buổi sáng Út Sen lặn bắt cá, hái bông trên sông Chín Khúc (`gather`); buổi tối nấu và phục vụ khách trên nhà bè của Má Tư (`quan`). Những gì mang về buổi sáng quyết định quán bán được món nào.

Lab Day 12 · AI SDLC · Test Contract v1.1. Thành viên và vai: [`TEAM.md`](TEAM.md).

## Chạy từ clone sạch (macOS / Linux, chỉ cần Python 3, không cài thêm gì)

```bash
git clone https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667.git
cd K5-L3B-LAB-Day12-AI-SDLC-6667
python3 -m chonoi.live --mode gather
```

Mở địa chỉ lệnh in ra (mặc định `http://127.0.0.1:8000/`). Muốn chơi buổi tối: `python3 -m chonoi.live --mode quan`.

**Chơi nối hai buổi:** mặc định, khi Gather kết thúc game tự chuyển sang Quán và mang theo kho:

```bash
python3 -m chonoi.live --mode gather
```

Muốn giữ Gather ở màn kết thúc và chạy Quán riêng bằng file kho:

```bash
python3 -m chonoi.live --mode gather --no-auto-transition --inventory-out kho.json
python3 -m chonoi.live --mode quan --inventory kho.json
```

## Điều khiển

| Phím | Buổi sáng (`gather`) | Buổi tối (`quan`) |
|---|---|---|
| WASD / mũi tên | Bơi (S / ↓ là lặn xuống) | Đi lại trong nhà bè |
| E | Cập bến (kết thúc buổi, giao giỏ) · hái bông khi ở mặt nước | Nấu ở bếp · bưng món · phục vụ ở bàn |
| Space | Bắt đàn cá khi đang lặn | — |
| R | Chơi lại | Chơi lại |

HUD buổi sáng: thời gian, oxy, Máu, giỏ. Buổi tối: kho khả dụng, món khách gọi, kiên nhẫn, trạng thái bếp, món trên tay, tiền, uy tín.

## Luật chính và cách tính điểm

- **Buổi sáng:** dưới nước mất oxy, nổi lên thì hồi. Hết oxy thì cứ 60 tick ngạt mất 1 Máu; hết 3 Máu thì ngất, mất cả giỏ. Giỏ chứa 12 ô. Cập bến hoặc hết giờ thì phần trong giỏ thành kho của quán.
- **Buổi tối:** khách đến theo lịch, gọi một trong 3 món nấu được từ kho và giữ nguyên liệu ngay. Nấu → bưng → phục vụ trước khi khách hết kiên nhẫn. Khách ăn xong trả tiền món; còn ≥ 50% kiên nhẫn lúc được phục vụ thì boa `floor(giá × 0.2)` và quán được +0.2 uy tín. Khách bỏ về vì chờ lâu: −0.5 uy tín. Uy tín trong [0, 5], bắt đầu 3.0.
- **Điểm** (ở mọi snapshot và dòng `end`):

  ```
  score = earned + 100 × floor(reputation)
  ```

  `earned` là tổng tiền thu (nghìn đồng, gồm boa). Ví dụ thu 72, uy tín 3.2 → `72 + 100 × 3 = 372`.

Số liệu đầy đủ ở [`game.contract.json`](game.contract.json); hợp đồng tích hợp ở [`docs/contracts/README.md`](docs/contracts/README.md).

## Test (1 lệnh)

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```

Smoke hai tiến trình (gather → file kho → quan) và lưu bằng chứng vào `docs/proof/phase-1/smoke-<sha>/`:

```bash
tools/smoke_p1.sh
```

## Headless (Test Contract)

```bash
python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out.jsonl [--scenario sc.json] [--inputs in.json] [--inventory-out kho.json]
python3 -m chonoi.headless --mode quan --seed 1 --ticks 600 --out out.jsonl [--inventory kho.json]
```

Mã thoát: `0` bình thường · `2` tham số/dữ liệu sai · `1` lỗi chạy. Cùng seed và đầu vào → JSONL và file kho giống từng byte.

## Sáng tạo của nhóm

Phase 1 chưa có phần tự sáng tạo; nhóm làm lõi đúng trước. Khi thêm, ghi ở đây kèm bằng chứng lõi vẫn đúng (phần thêm tắt ở headless).

## Tài liệu nhóm

[`TEAM.md`](TEAM.md) · [`AGENTS.md`](AGENTS.md) · [`docs/contracts/`](docs/contracts/README.md) · [`docs/clarify.md`](docs/clarify.md) · [`docs/verification/phase-1.md`](docs/verification/phase-1.md) · [`docs/proof/`](docs/proof/) · [`docs/plan/`](docs/plan/) · [`docs/ai-usage-log.md`](docs/ai-usage-log.md) · [`docs/retro.md`](docs/retro.md) · [`docs/standup.md`](docs/standup.md) · [`docs/members/`](docs/members/) · [`CREDITS.md`](CREDITS.md)

## Về lab

Yêu cầu từng phase mở theo giờ tại lab board **[Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)**. Chi tiết khung Python của giảng viên (cái gì có sẵn, đổi ngôn ngữ thế nào): [`docs/STARTER.md`](docs/STARTER.md).


## Phase 2 — Chơi trọn vòng ngày
```bash
python3 -m chonoi.live --mode day
python3 -m chonoi.headless --mode day --days 1 --seed 42 --ticks 22200 --out day.jsonl
tools/smoke_p2.sh
```
Live mặc định 5 Ngày; `--days 1..5` chọn số Ngày. Headless mặc định 1 Ngày. Bấm Chơi, xem lời dặn Má Tư, WASD bơi/đi, E hái/cập bến/nấu/bưng/phục vụ, Space bắt cá, Esc/P pause. Shop mua Bình oxy/Áo phao bằng nút, đóng sớm hoặc chờ 10 s hoạt động. Cấp mua áp dụng từ Ngày kế; earned và điểm không bị trừ khi mua. Thoát trở về màn lời chào để đóng thẻ trình duyệt.

Lõi đã bổ sung: vòng gather→quan→Shop, kế hoạch D1–D5, menu/intro/kết quả/tổng kết, pause cả Shop, HUD mục tiêu và quái, 6 tên món. Chưa bật các mở rộng weapon/net/snake/burn/vendor/ca_ho/settings. Nguồn: `docs/tickets/TICKET-02.md`; kiểm chứng: `docs/verification/phase-2.md`.
