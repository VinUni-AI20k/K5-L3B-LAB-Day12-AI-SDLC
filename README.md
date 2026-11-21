# Day 12 — AI SDLC: Quán Ăn Chợ Nổi — Nhóm T77

## Chạy game (từ clone sạch, macOS/Linux, chỉ cần Python 3)

```bash
git clone https://github.com/Ngochung1772k4/K5-L3B-LAB-Day12-AI-SDLC-T77.git && cd K5-L3B-LAB-Day12-AI-SDLC-T77
python3 -m chonoi.live --mode gather --inventory-out kho.json     # buổi sáng: mở địa chỉ in ra trong trình duyệt
python3 -m chonoi.live --mode quan --inventory kho.json           # buổi tối: quán dùng đúng kho mang về
```

Headless (Test Contract v1.0): `python3 -m chonoi.headless --mode gather|quan --seed 1 --ticks 600 --out out.jsonl` (thêm `--scenario`, `--inputs`, `--inventory`, `--inventory-out` theo [PRD-0 mục B](docs/prd/PRD-0.md)).

**Test (1 lệnh):** `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`

> Windows: nếu không có lệnh `python3`, copy `python.exe` thành `python3.exe` trong thư mục cài Python (smoke test gọi `headless_cmd` = `python3 -m chonoi.headless`).

## Điều khiển

| Phím | Buổi sáng (lặn & hái) | Buổi tối (quán) |
|---|---|---|
| WASD / mũi tên | Bơi (S/↓ = lặn xuống) | Đi lại |
| E | Hái nút trên mặt nước · cập bến (kết thúc buổi sáng) | Nấu ở bếp · bưng món chín · phục vụ ở bàn |
| Space | Bắt đàn cá khi đang lặn | — |
| R | Chơi lại | Chơi lại |

## Cách chơi và tính điểm

- **Sáng:** lặn tốn oxy (30 s), nổi lên hồi oxy. Hết oxy dưới nước thì cứ 1 s mất 1 Máu (3 Máu); hết Máu là ngất, mất cả giỏ. Giỏ chứa 12 món. Cập bến hoặc hết 3 phút thì giỏ thành kho của quán.
- **Tối:** khách gọi món nấu được từ kho và giữ nguyên liệu. Nấu → bưng → phục vụ trước khi khách hết kiên nhẫn (60 s). Phục vụ khi khách còn ≥ 50% kiên nhẫn thì được boa 20% và +0.2 uy tín; khách bỏ đi −0.5 uy tín.
- **Điểm** = `earned + 100 × floor(uy tín)` (tiền tính bằng nghìn đồng).

## Tài liệu của nhóm

[TEAM.md](TEAM.md) · [PRD-0](docs/prd/PRD-0.md) · [Hợp đồng tích hợp](docs/contracts/README.md) · [Chia việc Phase 1](docs/plan/phase-1-chia-viec.md) · [Kiểm chứng](docs/verification/phase-1.md) · [Clarify](docs/clarify.md) · [Nhật ký AI](docs/ai-usage-log.md)

## Sáng tạo của nhóm

(Chưa có. Phần thêm chỉ chạy ở `chonoi.live`, tắt ở headless; ghi kèm bằng chứng lõi vẫn đúng.)

---

# Đề bài gốc của lab

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
