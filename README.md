# Day 12 — AI SDLC: Quán Ăn Chợ Nổi

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

Tài liệu nhóm Math. [Kế hoạch Phase 1](docs/plan/phase-1.md) · [Ma trận kiểm chứng](docs/verification/phase-1.md) · [Câu hỏi cho PO](docs/clarify.md) · [Hướng dẫn chạy cho agent](AGENTS.md)

### Điều khiển

| Phím | Buổi sáng (gather) | Buổi tối (quan) |
|---|---|---|
| WASD / mũi tên | Bơi ngang và lặn/nổi | Đi trong nhà bè |
| E | Cập bến (trong bán kính bến) hoặc hái nút trên mặt nước | Nấu ở bếp, bưng món, phục vụ ở bàn |
| Space | Bắt cá khi đang lặn | — |
| R | Chơi lại | Chơi lại |
| Esc / P | Tạm dừng (từ Phase 2) | Tạm dừng (từ Phase 2) |

Từ Phase 2 game chơi theo vòng ngày (5 Ngày): Má Tư đọc món định nấu → lặn hái → mở quán → kết quả ngày → Shop mua Bình oxy / Áo phao. Headless một Ngày: `python3 -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --out day.jsonl`.

### Cách tính điểm

`score = earned + 100 × floor(reputation)`: `earned` là tổng tiền thu (nghìn đồng, gồm boa), `reputation` là uy tín 0–5 (bắt đầu 3.0; khách hết kiên nhẫn −0.5, khách boa +0.2).

### Mở rộng đã làm

> Nhóm 6 người cần ≥ 2 mục trong cả buổi (TICKET-02 mục 3). Mục có mã trong Test Contract thì khai ở `extensions` tại gốc `game.contract.json`.

| Mục | Mã `extensions` | Phase | Test / bằng chứng |
|---|---|---|---|
| (chưa chọn, PO chốt ở đầu Phase 3) | | | |

### Sáng tạo của nhóm

> Phase 1 làm lõi trước, chưa có phần sáng tạo. Mỗi ý tưởng thêm vào sẽ ghi ở đây kèm bằng chứng lõi vẫn đúng (headless tắt phần thêm, test vẫn xanh).

| Ý tưởng | Phase | Tắt ở headless thế nào | Bằng chứng lõi vẫn đúng |
|---|---|---|---|
| (chưa có) | | | |

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
