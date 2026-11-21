# Day 12 — AI SDLC: Quán Ăn Chợ Nổi

## Nhóm nhom6ae — Quán Ăn Chợ Nổi v1.0.0 (Contract v1.3)

### Yêu cầu môi trường
- **Python 3.9+** (chỉ dùng thư viện chuẩn, không cần `pip install`).
- **Trình duyệt web** (Chrome / Firefox / Safari / Edge) cho chế độ chơi có giao diện (`chonoi.live`).
- **Node.js** *(tùy chọn)* — chỉ cần nếu chạy công cụ kiểm HUD `tools/hud_check.py`.

### Chạy game từ clone sạch (≤ 3 lệnh, macOS / Linux)

```bash
git clone https://github.com/NgChiVinh/K5-L3B-LAB-Day12-AI-SDLC-nhom6ae.git && cd K5-L3B-LAB-Day12-AI-SDLC-nhom6ae
python3 -m chonoi.live --mode day --days 5         # mở http://127.0.0.1:8000/ chơi trọn vòng 5 Ngày (gather -> quan -> shop)
```

Hoặc chạy riêng 2 buổi nối qua file kho cá thể (Contract v1.2/v1.3):
```bash
python3 -m chonoi.live --mode gather --inventory-out /tmp/kho.json
python3 -m chonoi.live --mode quan --inventory /tmp/kho.json
```

### Điều khiển & luật chơi
- **Điều khiển:** `WASD` / phím mũi tên = bơi / đi · **`E`** = cập bến, hái (buổi sáng) · nấu, bưng, phục vụ (buổi tối) · **`Space`** = bắt cá · **`Esc` / `P`** = tạm dừng (pause) · **`R`** = chơi lại · trong Shop: bấm nút mua nâng cấp (`oxygen` / `hp`) và đóng Shop (`shop_done`).
- **Buổi sáng (`gather`):** lặn bắt cá (`Space`, dưới nước), nổi lên hái bông điên điển / bông súng / kèo nèo (`E`, mặt nước); tránh Cá Sấu Năm Chèo (M1 từ Ngày 1, M2 từ Ngày 3); oxy cạn thì ngạt mất Máu, hết Máu thì ngất và mất giỏ. Mỗi nguyên liệu là một cá thể `{id, kind, fresh}` hao `0.5/s` trong giỏ; `< 30` là ươn (không dùng nấu được).
- **Buổi tối (`quan`):** 2 bếp (`B1`, `B2`), 4 bàn (`T1`–`T4`), 6 món; kho hao `0.25/s` kể cả hàng giữ chỗ. Nấu trừ đúng cá thể giữ và chốt giá `floor(giá niêm yết × fresh TB / 100)`; giao khi kiên nhẫn ≥ 50% có boa `floor(giá chốt × 0.2)` (+0.2 uy tín); khách hết kiên nhẫn −0.5 uy tín.
- **Shop cuối ngày (`shop`):** mua nâng cấp Bình oxy (cấp 1: 200 → 45 s; cấp 2: 400 → 60 s) và Áo phao (cấp 1: 250 → 4 Máu; cấp 2: 500 → 5 Máu), trừ vào `money`, giữ nguyên `earned`, có hiệu lực từ Ngày kế tiếp.
- **Điểm:** `earned + 100 × floor(reputation)`.

### Các lệnh kiểm thử, headless, benchmark, soak & đóng gói
- **Test toàn bộ (1 lệnh):**
  ```bash
  PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
  ```
- **Headless (Test Contract v1.3):**
  ```bash
  python3 -m chonoi.headless --mode gather|quan|day --seed 1 --ticks 600 --out out.jsonl
  ```
- **Benchmark có render (1280×720, làm nóng 3 s, đo 30 s):**
  ```bash
  python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json
  ```
- **Soak headless (10 Ngày liên tiếp):**
  ```bash
  python3 -m chonoi.soak --seed 7 --days 10 --out soak.json
  ```
- **Đóng gói bản phát hành (tạo `.tar.gz` và `.zip` trong `dist/`):**
  ```bash
  python3 tools/package_release.py --version v1.0.0
  ```
- **Windows:** dùng `python`, đặt `PYTHONIOENCODING=utf-8`, test dùng `PYTHONPATH="tests;."` (xem [`AGENTS.md`](AGENTS.md)).
- Nhóm, vai, thỏa thuận: [`TEAM.md`](TEAM.md) · đề: [`docs/prd/`](docs/prd/) · bằng chứng: [`docs/verification/`](docs/verification/), [`docs/proof/`](docs/proof/) · thay đổi: [`CHANGELOG.md`](CHANGELOG.md) · bản quyền: [`LICENSE`](LICENSE), [`CREDITS.md`](CREDITS.md).

### Mở rộng đã làm
- **Cháy món (`burn`)** — khai trong `extensions` của [`game.contract.json`](game.contract.json) với `quan.burn_s: 20` (1200 tick). Món chín trên bếp đúng `1200` tick vẫn bưng được; từ `1201` tick trở đi bị cháy: mất món, bếp `idle` ngay, thử giữ lại nguyên liệu tươi cho đơn (`reserved` hoặc `unfulfillable`) và phát `dish_burnt`. Kiểm chứng bằng test hộp đen trong [`tests/test_p3_quan_fresh_burn.py`](tests/test_p3_quan_fresh_burn.py) (`PYTHONPATH=tests:. python3 -m unittest tests.test_p3_quan_fresh_burn -v`).

- **Bảng xếp hạng cục bộ (`leaderboard`)** — khai trong `extensions`. Lưu bền vững top 10 (`chonoi/leaderboard.py`), sắp điểm giảm dần, hòa thì mục ghi trước đứng trước (kể cả sau khi mở lại). Headless `--mode day` nhận cặp `--leaderboard <store.json> --player-name <tên>`: chỉ ghi một mục khi chạy đủ 5 Ngày chuẩn, không scenario, `reason: days_complete`; thiếu một cờ trong cặp hoặc sai mode → mã 2. Xuất bảng: `python3 -m chonoi.live --mode gather --export-leaderboard out.json [--leaderboard store.json]`. Kiểm chứng: [`tests/test_leaderboard.py`](tests/test_leaderboard.py), [`tests/test_leaderboard_run_cmd.py`](tests/test_leaderboard_run_cmd.py).

### Sáng tạo của nhóm
- Ưu tiên hoàn thiện lõi và mở rộng đúng Test Contract; không thêm phần sáng tạo ngoài contract vào headless để bảo toàn tính tất định.

---

> **Làm theo nhóm 4–6 người** · Dùng AI để xây game 2D qua **4 phase** trong **3 giờ**: Út Sen lặn bắt cá, hái rau trên mặt nước rồi tối mở quán phục vụ khách.
> **Yêu cầu từng phase mở đúng mốc giờ tại lab board:** **[Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)** (cần đăng nhập claude.ai; có trợ giảng AI cho từng phase).

## Bắt buộc (chỉ có thế)

Cách làm việc kỹ thuật là **tự do** (push thẳng, nhánh + PR, pair, có hay không CI…). Cái bắt buộc:

1. **Một repo chung:** trưởng nhóm **fork** repo này, đặt tên `K5-L3B-LAB-Day12-AI-SDLC-<ten-nhom>`, thêm mọi thành viên làm collaborator (*Settings → Collaborators*, quyền Write) và để repo **public** (giảng viên xem được, không cần mời).
2. **Cả nhóm cùng commit** bằng tài khoản GitHub của mình, mỗi người **≥ 3 commit có nội dung** (làm cặp thì ghi `Co-authored-by:`).
3. **Điền [`TEAM.md`](TEAM.md):** danh sách thành viên + thỏa thuận làm việc nhóm; sửa `team_size` trong [`game.contract.json`](game.contract.json). Commit của người không có trong `TEAM.md` không được tính.
4. **Gắn tag** `phase-1` … `phase-4` đúng hạn; chạy được tại từng tag.
5. **Ghi chép tối thiểu:** `docs/verification/phase-n.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md`, `docs/members/<handle>.md`.

## Bắt đầu nhanh

```bash
git clone <fork-của-nhóm> && cd <fork-của-nhóm>
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v        # smoke test
python3 -m chonoi.live --mode gather                                # chơi thử trên trình duyệt (tùy chọn)
```

Game cần chế độ **headless** theo Test Contract (`python3 -m chonoi.headless --mode gather|quan …`) để được chạy và chấm tự động. **Công nghệ không ràng buộc**: khung Python trong `chonoi/` chỉ là gợi ý, chi tiết ở [`docs/STARTER.md`](docs/STARTER.md).

## Tự do sáng tạo

Ngoài phần đề yêu cầu, nhóm được **thêm** nhân vật, loài cá/cây, sinh vật, món, bản đồ, cơ chế, câu chuyện, đồ họa, âm nhạc… với ba điều kiện: **không phá phần cố định** (tắt ở headless), ghi mục **"Sáng tạo của nhóm"** trong README của nhóm, và **làm lõi đúng trước**.

## Lịch 3 giờ

| Mốc | Phase | Hạn tag |
|---|---|---|
| 0:00 | Phase 1 (PRD-0) | `phase-1` trước 1:00 |
| 1:00 | Phase 2 | `phase-2` trước 1:55 |
| 1:55 | Phase 3 | `phase-3` trước 2:30 |
| 2:30 | Phase 4 | `phase-4` + Release `v1.0.0` trước 3:00 |

Hết giờ mỗi phase thì gắn tag rồi đi tiếp; chỗ chưa xong ghi trung thực trong bằng chứng.

## Đánh giá (100 điểm)

| Hạng mục | Điểm |
|---|---|
| Test tự động ẩn (headless, gồm kiểm tra lại phase trước) | 25 |
| Làm việc nhóm (một repo chung, chia việc, tích hợp, đổi yêu cầu) | 25 |
| Kiểm chứng & bằng chứng | 15 |
| Harness AI (AGENTS.md, skill, nhật ký dùng AI) | 10 |
| Đánh giá & retro | 10 |
| Chất lượng sản phẩm (đúng yêu cầu, mở rộng/sáng tạo) | 10 |
| Demo | 5 |

## Quy định

- Dùng AI thoải mái; **không sao chép repo của nhóm khác**; bằng chứng phải thật.
- Nhân vật, bối cảnh là bản gốc của lab; asset ngoài chỉ dùng CC0/CC-BY/MIT hoặc tự tạo, ghi nguồn trong `CREDITS.md`. Không commit API key, token, `.env`.
