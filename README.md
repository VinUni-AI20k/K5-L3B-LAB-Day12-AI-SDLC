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

Trên macOS hoặc Linux, cần Python 3.12 trở lên và trình duyệt. Chạy từ clone sạch bằng ba lệnh rồi mở URL được in ra.

```bash
git clone https://github.com/KN-16/K5-L3B-LAB-Day12-AI-SDLC-Phoenix
cd K5-L3B-LAB-Day12-AI-SDLC-Phoenix
python3 -m chonoi.live --mode day
```

Dùng **WASD hoặc phím mũi tên** để di chuyển. **E** hái rau, cập bến hoặc tương tác với bếp và bàn. **Space** bắt cá khi đang lặn. **P** hoặc **Esc** để tạm dừng. Khi chơi ca độc lập, **R** bắt đầu lại ca.

Bấm **Chơi**, xem mục tiêu nguyên liệu, chơi hai ca rồi dùng tiền trong Shop. Đóng Shop để bắt đầu Ngày tiếp theo hoặc xem tổng kết. Trong quán, theo HUD để xem nguyên liệu khả dụng, đơn gọi, kiên nhẫn, bếp và món đang cầm. Điểm bằng tổng thu (gồm boa) cộng 100 nhân phần nguyên của uy tín. Tiền tính theo nghìn đồng.

Chạy bộ test bằng `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`.

Chơi hai ca riêng bằng `mkdir -p tmp && python3 -m chonoi.live --mode gather --inventory-out tmp/kho.json`. Khi gather kết thúc và ghi kho, dừng tiến trình bằng Ctrl+C rồi chạy `python3 -m chonoi.live --mode quan --inventory tmp/kho.json`.

Chạy headless một Ngày với `mkdir -p tmp && python3 -m chonoi.headless --mode day --days 1 --seed 42 --ticks 22200 --out tmp/day.jsonl`.

Game có các chế độ **headless** `gather`, `quan` và `day` theo Test Contract. [Tài liệu khung Python](docs/STARTER.md) và [hợp đồng tích hợp Phase 2](docs/contracts/phase-2.md) mô tả các luồng chạy.

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
