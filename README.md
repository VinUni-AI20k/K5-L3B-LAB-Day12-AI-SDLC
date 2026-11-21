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

## Tự do sáng tạo

Ngoài phần đề yêu cầu, nhóm được **thêm** nhân vật, loài cá/cây, sinh vật, món, bản đồ, cơ chế, câu chuyện, đồ họa, âm nhạc… với ba điều kiện: **không phá phần cố định** (tắt ở headless), ghi mục **"Sáng tạo của nhóm"** trong README của nhóm, và **làm lõi đúng trước**.

### Sáng tạo của nhóm (Nhóm Hallucination)
Nhóm đã tích hợp 3 tính năng mở rộng đặc sắc mang đậm bản sắc sông nước miền Tây trên client trực tiếp (`chonoi/web/index.html`):
1. **Hệ thống âm thanh tương tác (Web Audio API)**: Tổng hợp âm thanh tự động (không phụ thuộc file ngoài): tiếng tủm khi lặn (`dive`), tiếng nhô lên thở (`surface`), tiếng ting vui tai khi bắt cá / hái hoa, tiếng xèo xèo khi nấu bếp, tiếng leng keng khi nhận tiền & boa, và cảnh báo âm thanh khi oxy dưới 25%.
2. **Hệ thống Lời thoại Nam Bộ & Hộp thoại nhân vật**: Nhân vật có lời thoại tương tác theo thời gian thực: Má Tư dặn dò con gái, Út Sen cảm thán khi lặn/bắt cá/hụt hơi, và thực khách khen ngợi *"Món ngon bá cháy bọ chét luôn cô chủ nhỏ ơi! Thối tiền khỏi thối nghen!"*.
3. **Hiệu ứng đồ họa môi trường trên Canvas**: Sóng nước nhấp nhô trên mặt sông Chín Khúc, bọt khí nước (`bubbles`) nổi lên khi bơi lặn, khói bếp bốc lên từ bếp B1 và ánh đèn vàng lung linh trên sàn gỗ nhà bè Má Tư.

#### Phase 2 · Giao diện trọn vòng ngày (TV5)
Chơi trọn 5 Ngày trên trình duyệt: `python3 -m chonoi.live --mode day` (thêm `--days 2` để thử nhanh, `--speed 10` để tua nhanh ca chơi khi demo).

| Phím | Tác dụng |
|---|---|
| WASD / mũi tên | bơi (sáng) · đi (tối) |
| E | hái bông, cập bến · nấu, bưng, dọn món |
| Space | bắt cá (dưới nước) |
| Esc / P | tạm dừng (Tiếp tục · Cài đặt · Về menu) |
| Enter / phím bất kỳ | qua màn DayIntro, EveningIntro, DayResult |
| 1 / 2 · Enter | Shop: mua Bình oxy / Áo phao · đóng Shop |
| F3 / F2 | hiện FPS / nhật ký event (QA) |

Điểm = `earned + 100 × floor(uy tín)`. Màn hình: Menu → DayIntro (Má Tư đọc món + nguyên liệu) → Lặn & Hái (HUD đã lấy/cần) → EveningIntro (nhập kho, món nấu được) → Mở Quán → DayResult → Shop → Summary.

4. **Cài đặt âm thanh**: âm lượng Tổng / Nhạc nền / Hiệu ứng lưu trong trình duyệt giữa các lần mở; nhạc nền ngũ cung kiểu đàn tranh tự tổng hợp.
5. **Nhân vật & cảnh vẽ tay trên canvas**: Út Sen đội nón lá, bờ dừa lúc bình minh, tia nắng dưới nước, đèn lồng nhà bè, bong bóng gọi món có vòng kiên nhẫn.
6. **Chợ Chú Sáu (mở rộng `vendor` của TICKET-02, bản cửa sổ chơi)**: trong Shop bán kho dư (cá lóc 20k, cá linh 8k, cá kèo 10k, mỗi loại bông/kèo nèo 5k; cộng money và earned) và mua lại giá `floor(giá × 1.5)`, hàng mua giao thẳng vào kho quán tối Ngày kế, tách khỏi `gather_end.inventory`; phát `vendor_trade` / `buy_failed(out_of_stock|funds|unknown)`. Chỉ chạy ở cửa sổ chơi, DaySim headless chưa có lệnh vendor nên **chưa** khai `vendor` ở `extensions`.
7. **Thời tiết theo Ngày** (chỉ hình + tiếng): D1 nắng, D2 sương sớm, D3 mưa lâm râm (có tiếng mưa), D4 gió chướng (sóng lớn, lá bay), D5 nắng. Má Tư nhắc thời tiết ở DayIntro.
8. **Chuyện Má Tư kể**: 5 mẩu chuyện gốc về chợ nổi hiện ở DayResult, mở theo uy tín (D1 luôn mở, D5 cần ≥ 3.5); Summary đếm số chuyện đã nghe.
9. **Khách quen có tên**: Ông Ba vé số, Cô Tư áo dài, Chú Năm ghe lúa, Bé Bi, Dì Bảy bán bông, Anh Sáu xe ôm — gán theo id đơn, có lời chào/khen/than riêng. Chỉ là lớp hiển thị, không đổi luật chọn món.

Cửa sổ chơi dùng **cùng DaySim với headless** (`runner.Session("day")`); `chonoi/live_day.py` chỉ thêm màn chờ UI, gộp số liệu và Chợ Chú Sáu, không đụng headless.

**Mở rộng đã làm (nhóm 5 người, ≥ 1 mục):** *Settings & âm thanh* — âm lượng Master/Music/SFX lưu giữa các lần mở (mục này không có mã trong Test Contract nên không khai `extensions`). Bằng chứng: [docs/verification/phase-2.md](docs/verification/phase-2.md) mục 4. QA một lệnh: `python3 tools/qa_p2.py` → [docs/proof/phase-2/qa-report.md](docs/proof/phase-2/qa-report.md).

> **Bằng chứng lõi vẫn đúng**: Các hiệu ứng sáng tạo được đóng gói hoàn toàn trong client web (`index.html`), không tác động đến logic tick hay sự kiện của mô phỏng headless. Test contract và smoke test chạy độc lập đạt 100% (xem `docs/verification/phase-1.md`).

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
