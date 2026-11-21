# Day 12 — AI SDLC: Quán Ăn Chợ Nổi (Nhóm CSCD)

> **Nhóm 5 thành viên (`CSCD`)** · Game 2D quản lý quán ăn miền Tây Nam Bộ qua **4 phase** (Test Contract v1.0): Út Sen lặn bắt cá, hái rau trên sông Chín Khúc vào buổi sáng (`gather`) rồi tối mở quán trên nhà bè phục vụ khách (`quan`).

## Chạy nhanh từ clone sạch (macOS / Linux, ≤ 3 lệnh)

Yêu cầu Python 3 (chỉ dùng thư viện chuẩn, không cần cài gói ngoài):

```bash
git clone https://github.com/common-maker/K5-L3B-LAB-Day12-AI-SDLC-CSCD.git && cd K5-L3B-LAB-Day12-AI-SDLC-CSCD
python3 -m chonoi.live --mode gather --inventory-out kho.json
python3 -m chonoi.live --mode quan --inventory kho.json
```

Mở địa chỉ in ra trên terminal (mặc định `http://127.0.0.1:8000/`) bằng trình duyệt để chơi từng buổi. *(Trên Windows nếu thiếu `python3`, dùng `python` cho lệnh chơi thử.)*

## Điều khiển

| Phím | Chế độ `gather` (Buổi sáng) | Chế độ `quan` (Buổi tối) |
|---|---|---|
| `WASD` / Phím mũi tên | Bơi theo `[x, d]` | Đi lại trên nhà bè `[x, z]` |
| `E` (`interact`) | Cập bến (trong vùng bến) hoặc hái rau (mặt nước) | Nấu món (bếp rảnh), bưng món (bếp xong), phục vụ (bàn) |
| `Space` (`catch`) | Bắt đàn cá khi đang lặn dưới nước | — |
| `R` | Chơi lại từ đầu (`chonoi.live`) | Chơi lại từ đầu (`chonoi.live`) |

## Cách tính điểm & Luật ngắn

- **Công thức điểm:** `score = earned + 100 × floor(reputation)` (uy tín khởi đầu `3.0`, kẹp trong `[0, 5]`; tiền tính theo nghìn đồng).
- **Thực đơn cố định (3 món):**
  - **Cá lóc nướng trui** (`ca_loc_nuong_trui`): `ca_loc ×1`, nấu `6s`, giá `60k`
  - **Gỏi bông súng** (`goi_bong_sung`): `bong_sung ×2`, nấu `4s`, giá `40k`
  - **Lẩu cá linh bông điên điển** (`lau_ca_linh_dien_dien`): `ca_linh ×3 + bong_dien_dien ×1`, nấu `10s`, giá `120k`
- **Boa & Uy tín:** Phục vụ khi tỷ lệ kiên nhẫn còn lại `>= 0.5` được boa `floor(base_price × 0.2)`; thu tiền có boa cộng `+0.2` uy tín; khách chờ hết kiên nhẫn bỏ đi trừ `-0.5` uy tín; khách chờ rời lúc hết giờ (`closing`) không trừ uy tín.

## Chạy test & Headless (1 lệnh)

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v    # chạy toàn bộ unit + smoke test
python3 tools/check_team.py                                     # kiểm tra danh sách thành viên TEAM.md
```

**Smoke test hộp đen 2 tiến trình (PRD-0 mục G):**

```bash
python3 -m chonoi.headless --mode gather --seed 42 --scenario docs/proof/phase-1/dock.json --inputs docs/proof/phase-1/dock-inputs.json --ticks 1 --out /tmp/gather.jsonl --inventory-out /tmp/catch.json
python3 -m chonoi.headless --mode quan --seed 42 --inventory /tmp/catch.json --ticks 0 --out /tmp/quan.jsonl
```

Bằng chứng chạy thật và ma trận truy vết xem tại [`docs/proof/phase-1/smoke-2proc-log.txt`](docs/proof/phase-1/smoke-2proc-log.txt) và [`docs/verification/phase-1.md`](docs/verification/phase-1.md). Chi tiết khung kỹ thuật ở [`docs/STARTER.md`](docs/STARTER.md).

## Hợp đồng file kho (`gather` → `quan`)

File kho chỉ chứa khóa `"items"` ánh xạ 4 loại nguyên liệu (`ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`) sang số nguyên không âm, bỏ khóa bằng `0` (kho rỗng là `{"items":{}}`):

```json
{"items":{"bong_sung":2,"ca_loc":1}}
```

Xem chi tiết hợp đồng tại [`docs/contracts/README.md`](docs/contracts/README.md) và ví dụ mẫu tại [`docs/contracts/inventory.sample.json`](docs/contracts/inventory.sample.json).

## Sáng tạo của nhóm (tắt ở headless)

Phần mở rộng hiển thị chỉ chạy ở client trình duyệt [`chonoi/web/index.html`](chonoi/web/index.html) (và route static `/assets/` trong [`chonoi/live.py`](chonoi/live.py)), hoàn toàn không tác động đến `chonoi.headless`:
- Thay hình khối cá mặc định bằng sprite pixel art trong `assets/fish/` (`ca_loc`, `ca_linh`), giữ fallback hình khối khi ảnh chưa tải.
- Nâng cấp giao diện & HUD sang phong cách **pixel art + animation 60 FPS**: bộ icon pixel offscreen (`PIXEL_ICON`), thanh đo chia đốt (`pixelBar`), nội suy mượt vị trí & thanh chỉ số, bóng đổ chữ pixel, popup sự kiện bay lên, bối cảnh sông ánh hồng/dừa nước/phù sa, Út Sen áo bà ba khăn rằn kính lặn, nhà bè đèn dây vàng & khói bếp.
- HUD đọc trực tiếp `snapshot`: hiển thị **kho khả dụng** (đã trừ phần khách đang giữ chỗ), tên món tiếng Việt, cảnh báo sắp ngạt (`NGẠT`) và cảnh báo `GIỎ ĐẦY!`.
- **Bằng chứng lõi vẫn đúng:** [`docs/proof/phase-1/unittest-output.txt`](docs/proof/phase-1/unittest-output.txt) (**105/105 test pass**, gồm toàn bộ `test_smoke_p1.py`, `test_gather_lat1.py`, `test_gather_lat2.py`, `test_lat3_khach.py`, `test_lat4_quan.py` và `test_e_qa_p1.py`) và [`docs/proof/phase-1/smoke-2proc-log.txt`](docs/proof/phase-1/smoke-2proc-log.txt) (`PASS`).

## Lịch 3 giờ & Tài liệu nhóm

| Mốc | Phase | Hạn tag |
|---|---|---|
| 0:00 | Phase 1 (PRD-0) | `phase-1` trước 1:00 |
| 1:00 | Phase 2 | `phase-2` trước 1:55 |
| 1:55 | Phase 3 | `phase-3` trước 2:30 |
| 2:30 | Phase 4 | `phase-4` + Release `v1.0.0` trước 3:00 |

Tài liệu chính: [`TEAM.md`](TEAM.md) · [`AGENTS.md`](AGENTS.md) · [`CREDITS.md`](CREDITS.md) · [`docs/plan/phase-1.md`](docs/plan/phase-1.md) · [`docs/verification/phase-1.md`](docs/verification/phase-1.md) · [`docs/clarify.md`](docs/clarify.md) · [`docs/ai-usage-log.md`](docs/ai-usage-log.md).

## Quy định

- Không sao chép repo của nhóm khác; bằng chứng chạy phải là kết quả thật trên repo.
- Asset ngoài chỉ dùng CC0/CC-BY/MIT hoặc tự tạo, ghi nguồn đầy đủ trong [`CREDITS.md`](CREDITS.md). Không commit API key, token, `.env` hay file `*.jsonl`.
