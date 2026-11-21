# Quán Ăn Chợ Nổi — nhóm G2026

Game 2D quản lý quán ăn miền Tây. Buổi sáng Út Sen lặn bắt cá, hái bông trên sông Chín Khúc. Buổi tối em nấu và phục vụ khách trên nhà bè của Má Tư. Những gì mang về từ buổi sáng quyết định buổi tối bán được món gì.

**Nhóm G2026 (3 người)**, chi tiết vai và thỏa thuận ở [`TEAM.md`](TEAM.md):

| Thành viên | GitHub | Phần chính |
|---|---|---|
| Trương Đặng Minh Khuê | `mKhaiTruong` | hợp đồng `docs/contracts/`, `scenario.py`, test/proof, tag (Integrator, QA lead) |
| Phong | `trinhtuanphong123` | `chonoi/sim/gather.py` (lát 1 + 2), README, chơi thử HUD (Scrum/Release) |
| Khánh | `qockhah253` | `chonoi/sim/quan.py` (lát 3 + 4), `docs/clarify.md` (PO) |

## Chạy từ clone sạch (macOS / Linux, 3 lệnh)

Chỉ cần Python 3, không phải `pip install` vì code chỉ dùng thư viện chuẩn.

```bash
git clone https://github.com/mKhaiTruong/K5-L3B-LAB-Day12-AI-SDLC-G2026.git
cd K5-L3B-LAB-Day12-AI-SDLC-G2026
python3 -m chonoi.live --mode gather
```

Mở địa chỉ được in ra (mặc định `http://127.0.0.1:8000/`) bằng trình duyệt.

### Chơi trọn một ngày: sáng → tối qua file kho

```bash
python3 -m chonoi.live --mode gather --inventory-out kho.json   # buổi sáng: cập bến hoặc hết giờ thì ghi kho.json
python3 -m chonoi.live --mode quan --inventory kho.json         # buổi tối: quán mở với đúng kho đã mang về
```

Thêm `--seed N` để đổi lượt khách và `--port N` để đổi cổng.

### Chạy headless (Test Contract v1.0, dùng để chấm tự động)

```bash
python3 -m chonoi.headless --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json \
  --ticks 1 --out gather.jsonl --inventory-out catch.json
python3 -m chonoi.headless --mode quan --seed 42 --inventory catch.json --ticks 0 --out quan.jsonl
```

Trong đó `dock.json` là `{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}` và `dock-inputs.json` là `{"frames":[{"tick":0,"interact":true}]}`. Kết quả: `catch.json` = `{"items":{"bong_sung":2,"ca_loc":1}}`, và snapshot quán ở tick 0 có đúng `stock` đó. Các cờ đầy đủ ở PRD-0 mục B; `headless_cmd` khai trong [`game.contract.json`](game.contract.json).

## Điều khiển

| Phím | Buổi sáng (gather) | Buổi tối (quan) |
|---|---|---|
| WASD / mũi tên | bơi (S/↓ là lặn xuống) | đi lại trong nhà bè |
| E | ở bến: cập bến, kết thúc buổi · ở mặt nước gần nút: hái bông | nấu ở bếp B1 · bưng món · phục vụ ở bàn T1 |
| Space | bắt đàn cá gần nhất (chỉ khi đang lặn) | — |
| R | chơi lại | chơi lại |

**HUD:** buổi sáng có thời gian, thanh oxy, Máu (♥) và giỏ (số ô, loại hàng). Buổi tối có thời gian, tiền, uy tín, điểm, kho, món khách gọi kèm thanh kiên nhẫn, trạng thái bếp và món trên tay.

## Luật chính

- **Buổi sáng:**
  - Dưới nước (d > 0.5 m) mất 1 tick oxy mỗi tick (tối đa 30 s). Ở mặt nước hồi 6 tick oxy mỗi tick.
  - Hết oxy mà vẫn ở dưới nước thì cứ 60 tick mất 1 Máu. Mất hết 3 Máu thì ngất: mất toàn bộ giỏ, kho rỗng.
  - Hái bông ở mặt nước, nút mọc lại sau 20 s.
  - Bắt cá khi lặn: cá linh cho 3, cá lóc cho 1, hồi chiêu 0.5 s. Giỏ chứa tối đa 12.
  - Cập bến hoặc hết giờ thì mang giỏ về kho.
- **Buổi tối:**
  - Khách đến theo lịch, gọi món nấu được bằng kho và giữ chỗ nguyên liệu ngay khi gọi.
  - Người chơi nấu → bưng → phục vụ trước khi khách hết kiên nhẫn. Khách ăn xong thì trả tiền, phục vụ sớm thì được boa.
  - Khách bỏ về làm giảm uy tín.
- Mọi số liệu nằm trong [`game.contract.json`](game.contract.json) (preset v1.0); luật chỉ đọc từ đó.

## Cách tính điểm

```
score = earned + 100 × floor(reputation)
```

- `earned`: tổng tiền thu cả lượt (tiền món + boa), đơn vị **nghìn đồng**.
- `reputation`: uy tín, bắt đầu 3.0, kẹp trong [0, 5]. Boa thì +0.2, khách bỏ về vì hết kiên nhẫn thì −0.5.
- Hệ số 100 là `score.reputation_multiplier` trong `game.contract.json`.

Ví dụ: thu 72k, uy tín 3.2 → điểm = 72 + 100 × 3 = **372**.

## Chạy test (1 lệnh)

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```

**Windows (PowerShell):** tạo shim một lần (`python -m venv .venv`, rồi `copy .venv\Scripts\python.exe .venv\Scripts\python3.exe`). Sau đó:

```powershell
$env:PATH = "$PWD\.venv\Scripts;$env:PATH"; $env:PYTHONPATH = "tests;."; $env:PYTHONUTF8 = "1"; python3 -m unittest discover -s tests -v
```

Bộ test gồm: smoke hộp đen theo Test Contract (`test_smoke_p1.py`), luật buổi sáng (`test_gather_lat1.py`: oxy, ngạt, ngất · `test_gather_lat2.py`: hái, bắt cá), luật quán (`test_quan.py`), kiểm scenario mã 2 (`test_scenario_gather.py`, `test_scenario_quan.py`), cửa sổ thử (`test_live.py`), khung Python (`test_python_starter_units.py`), danh sách nhóm (`test_team_check.py`).

## Hợp đồng file kho (sáng → tối)

```json
{"items": {"<kind>": <số nguyên ≥ 0>}}
```

- `kind` ∈ `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`. Bỏ khóa có lượng 0; kho rỗng là `{"items":{}}`.
- Ví dụ hợp lệ: `{"items":{"bong_sung":2,"ca_loc":1}}`.
- Buổi sáng ghi đúng một lần khi kết thúc (cập bến, hết giờ, hoặc ngất thì ghi kho rỗng). Buổi tối đọc lúc khởi tạo; sai schema thì thoát mã 2.

Chi tiết schema, giao diện sim ↔ UI và bảng sự kiện: [`docs/contracts/README.md`](docs/contracts/README.md).

## Sáng tạo của nhóm

Chưa có ở Phase 1: nhóm làm lõi đúng trước theo PRD-0. Khi thêm, phần sáng tạo sẽ được ghi ở đây kèm bằng chứng lõi vẫn đúng (tắt ở headless).

## Hạn chế đã biết (Phase 1)

- HUD buổi tối in `stock` là tồn vật lý, **đã gồm phần khách đang giữ chỗ**, nên chưa đúng "kho khả dụng" theo PRD. Ví dụ: kho có 3 cá lóc, khách gọi cá lóc nướng trui, HUD vẫn hiện "Cá lóc×3" thay vì 2. Snapshot và luật vẫn đúng PRD-0 mục D. Đã báo Integrator; sửa ở `chonoi/web/index.html` (file khung).
- Hai giả định đang chờ Anh Năm xác nhận ([`docs/clarify.md`](docs/clarify.md) #4, #5): `random_fish: true` = 6 đàn `fish_initial` đứng yên; bắt cá khi giỏ thiếu chỗ thì không đặt hồi chiêu.

## Tài liệu của nhóm

[`TEAM.md`](TEAM.md) · [`AGENTS.md`](AGENTS.md) · [`docs/plan/phase-1.md`](docs/plan/phase-1.md) · [`docs/verification/phase-1.md`](docs/verification/phase-1.md) · [`docs/clarify.md`](docs/clarify.md) · [`docs/ai-usage-log.md`](docs/ai-usage-log.md) · [`docs/STARTER.md`](docs/STARTER.md) (chi tiết khung Python)

---

## Đề bài gốc (giảng viên): Day 12 — AI SDLC

> **Làm theo nhóm 4–6 người** · Dùng AI để xây game 2D qua **4 phase** trong **3 giờ**: Út Sen lặn bắt cá, hái rau trên mặt nước rồi tối mở quán phục vụ khách.
> **Yêu cầu từng phase mở đúng mốc giờ tại lab board:** **[Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)** (cần đăng nhập claude.ai; có trợ giảng AI cho từng phase).

### Bắt buộc (chỉ có thế)

Cách làm việc kỹ thuật là **tự do** (push thẳng, nhánh + PR, pair, có hay không CI…). Cái bắt buộc:

1. **Một repo chung:** trưởng nhóm **fork** repo này, đặt tên `K5-L3B-LAB-Day12-AI-SDLC-<ten-nhom>`, thêm mọi thành viên làm collaborator (*Settings → Collaborators*, quyền Write) và để repo **public** (giảng viên xem được, không cần mời).
2. **Cả nhóm cùng commit** bằng tài khoản GitHub của mình, mỗi người **≥ 3 commit có nội dung** (làm cặp thì ghi `Co-authored-by:`).
3. **Điền [`TEAM.md`](TEAM.md):** danh sách thành viên + thỏa thuận làm việc nhóm; sửa `team_size` trong [`game.contract.json`](game.contract.json). Commit của người không có trong `TEAM.md` không được tính.
4. **Gắn tag** `phase-1` … `phase-4` đúng hạn; chạy được tại từng tag.
5. **Ghi chép tối thiểu:** `docs/verification/phase-n.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md`, `docs/members/<handle>.md`.

### Bắt đầu nhanh

```bash
git clone <fork-của-nhóm> && cd <fork-của-nhóm>
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v        # smoke test
python3 -m chonoi.live --mode gather                                # chơi thử trên trình duyệt (tùy chọn)
```

Game cần chế độ **headless** theo Test Contract (`python3 -m chonoi.headless --mode gather|quan …`) để được chạy và chấm tự động. **Công nghệ không ràng buộc**: khung Python trong `chonoi/` chỉ là gợi ý, chi tiết ở [`docs/STARTER.md`](docs/STARTER.md).

### Tự do sáng tạo

Ngoài phần đề yêu cầu, nhóm được **thêm** nhân vật, loài cá/cây, sinh vật, món, bản đồ, cơ chế, câu chuyện, đồ họa, âm nhạc… với ba điều kiện: **không phá phần cố định** (tắt ở headless), ghi mục **"Sáng tạo của nhóm"** trong README của nhóm, và **làm lõi đúng trước**.

### Lịch 3 giờ

| Mốc | Phase | Hạn tag |
|---|---|---|
| 0:00 | Phase 1 (PRD-0) | `phase-1` trước 1:00 |
| 1:00 | Phase 2 | `phase-2` trước 1:55 |
| 1:55 | Phase 3 | `phase-3` trước 2:30 |
| 2:30 | Phase 4 | `phase-4` + Release `v1.0.0` trước 3:00 |

Hết giờ mỗi phase thì gắn tag rồi đi tiếp; chỗ chưa xong ghi trung thực trong bằng chứng.

### Đánh giá (100 điểm)

| Hạng mục | Điểm |
|---|---|
| Test tự động ẩn (headless, gồm kiểm tra lại phase trước) | 25 |
| Làm việc nhóm (một repo chung, chia việc, tích hợp, đổi yêu cầu) | 25 |
| Kiểm chứng & bằng chứng | 15 |
| Harness AI (AGENTS.md, skill, nhật ký dùng AI) | 10 |
| Đánh giá & retro | 10 |
| Chất lượng sản phẩm (đúng yêu cầu, mở rộng/sáng tạo) | 10 |
| Demo | 5 |

### Quy định

- Dùng AI thoải mái; **không sao chép repo của nhóm khác**; bằng chứng phải thật.
- Nhân vật, bối cảnh là bản gốc của lab; asset ngoài chỉ dùng CC0/CC-BY/MIT hoặc tự tạo, ghi nguồn trong `CREDITS.md`. Không commit API key, token, `.env`.
