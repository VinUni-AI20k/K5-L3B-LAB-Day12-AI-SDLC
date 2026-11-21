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

## Bắt đầu nhanh (macOS / Linux, ≤ 3 lệnh)

```bash
git clone <fork-của-nhóm> && cd <fork-của-nhóm>
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v        # 1 lệnh chạy test
python3 -m chonoi.live --mode gather                                # chơi thử trên trình duyệt
```

### Demo trọn vòng (Buổi sáng → Cập bến xuất kho → Buổi tối)

```bash
python3 -m chonoi.live --mode gather --inventory-out kho.json       # Lặn & hái, nhấn E tại bến để xuất kho
python3 -m chonoi.live --mode quan --inventory kho.json             # Mở quán tối với kho vừa thu hoạch
```

### Phím điều khiển
- `WASD` / `Phím mũi tên`: Bơi (buổi sáng) / Đi lại (buổi tối)
- `E`: Cập bến hoặc hái rau (buổi sáng) · Nấu / Lấy món / Phục vụ (buổi tối)
- `Space`: Bắt cá (khi đang lặn dưới nước)
- `P` / `Esc`: Tạm dừng
- `R`: Chơi lại từ đầu

### Công thức tính điểm
```text
score = earned + 100 × floor(reputation)
```
Trong đó `earned` là tổng tiền thu được (tiền món + tiền boa, đơn vị nghìn đồng) và `reputation` là điểm uy tín của quán.

Game cần chế độ **headless** theo Test Contract (`python3 -m chonoi.headless --mode gather|quan …`) để được chạy và chấm tự động. **Công nghệ không ràng buộc**: khung Python trong `chonoi/` chỉ là gợi ý, chi tiết ở [`docs/STARTER.md`](docs/STARTER.md).

## Tự do sáng tạo

Ngoài phần đề yêu cầu, nhóm được **thêm** nhân vật, loài cá/cây, sinh vật, món, bản đồ, cơ chế, câu chuyện, đồ họa, âm nhạc… với ba điều kiện: **không phá phần cố định** (tắt ở headless), ghi mục **"Sáng tạo của nhóm"** trong README của nhóm, và **làm lõi đúng trước**.

## Mở rộng đã chọn của nhóm Banana (Extensions)

Nhóm 6 người hoàn thành 2 mở rộng theo yêu cầu của lab:
1. **Cháy món (`burn`)** (TV4 - Quân phụ trách):
   - Món chín ở bếp nếu để quá 20s (`burn_s: 20` tương đương 1.200 tick) sẽ bị cháy.
   - Khi `ready_ticks > 1200`: phát sự kiện `dish_burnt`, giải phóng bếp về `idle`.
   - Hệ thống tự động kiểm tra kho để giữ lại nguyên liệu (`reserved`) hoặc chuyển đơn sang `unfulfillable` nếu thiếu nguyên liệu tươi.
   - Kiểm chứng đầy đủ qua test suite `tests/test_tv4_phase2.py`, `tests/test_tv4_phase3.py`.
2. **Thiết lập âm thanh (`settings/audio`)** (TV5 - Cường phụ trách):
   - Cho phép người chơi tùy chỉnh riêng âm lượng Master, Music và SFX trên giao diện.
   - Thiết lập được lưu bền vững qua các phiên chơi.

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
