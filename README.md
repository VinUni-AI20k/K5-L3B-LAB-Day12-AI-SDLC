# Day 12 — AI SDLC: Quán Ăn Chợ Nổi

> **Làm theo nhóm 4–6 người** · Dùng AI để xây game 2D qua **4 phase** trong **3 giờ**: Út Sen lặn bắt cá, hái rau trên mặt nước rồi tối mở quán phục vụ khách.
> **Yêu cầu từng phase mở đúng mốc giờ tại lab board:** **[Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)** (cần đăng nhập claude.ai; có trợ giảng AI cho từng phase).

## Nhóm ChoNoiCaMau — chạy game

Thành viên và vai trò: [`TEAM.md`](TEAM.md). Yêu cầu từng phase (bản chép): [`docs/prd/`](docs/prd/). Chỉ cần Python 3 với thư viện chuẩn (nhóm đã chạy với 3.11 và 3.12), không cài thêm gì.

**Chạy từ clone sạch (macOS / Linux, 3 lệnh):**

```bash
git clone https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau.git && cd K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v      # test của nhóm (1 lệnh)
python3 -m chonoi.live --mode gather --inventory-out kho.json    # chơi buổi sáng, mở địa chỉ in ra
```

- **Buổi tối:** chạy `python3 -m chonoi.live --mode quan --inventory kho.json`; quán nhận kho buổi sáng mang về.
- **Windows (PowerShell):** đặt `$env:PYTHONPATH="tests;."` rồi chạy `python3 -m unittest discover -s tests -v`. Nếu báo không thấy `python3`, xem ghi chú Windows trong [`AGENTS.md`](AGENTS.md).

**Headless (Test Contract v1.0):**
`python3 -m chonoi.headless --mode gather|quan --seed 1 --ticks 600 --out out.jsonl [--scenario f.json] [--inputs f.json] [--inventory kho.json | --inventory-out kho.json]`

**Điều khiển:**
- **WASD / mũi tên:** bơi (sáng) hoặc đi (tối). Ở buổi sáng, phím xuống là lặn sâu hơn.
- **E:** cập bến hoặc hái nút trên mặt nước (sáng); nấu, bưng, phục vụ (tối).
- **Space:** bắt đàn cá khi đang dưới nước.
- **R:** chơi lại.

**Cách tính điểm** (mọi snapshot và dòng `end`): `điểm = earned + 100 × floor(uy tín)`.
- `earned` là tổng thu của lượt, gồm tiền món và tiền boa, đơn vị nghìn đồng.
- Uy tín bắt đầu từ 3.0, kẹp trong [0, 5].
  - Khách được boa thì +0.2.
  - Khách hết kiên nhẫn bỏ đi khi ca còn giờ thì −0.5.

**Tiến độ** (ghi trung thực):
- Phase 1: gather (lát 1, 2) và quán lát 3 xong. Quán lát 4 (bếp, phục vụ, tiền) chưa xong.
- Chi tiết: [`docs/verification/phase-1.md`](docs/verification/phase-1.md).

**Sáng tạo của nhóm:** chưa có (làm lõi đúng trước).

---

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
