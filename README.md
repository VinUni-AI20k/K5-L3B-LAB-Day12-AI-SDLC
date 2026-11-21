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
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v        # Chạy toàn bộ 57 tests bằng 1 lệnh
python3 -m chonoi.live --mode gather                                # chơi thử trên trình duyệt (WASD, E, Space, R)
```

### Điều khiển & Phím bấm
- **WASD / Phím mũi tên:** Di chuyển thuyền lặn (Gather: `[x, d]`) hoặc người phục vụ (Quán: `[x, z]`).
- **E / Phím bấm Tương tác (`interact`):** Cập bến (Gather), Bật bếp nấu / Bưng món / Phục vụ bàn (Quán).
- **Space (`catch`):** Bắt cá dưới nước khi nằm trong bán kính tương tác (Gather).
- **R:** Reset / Bắt đầu lại ca.

### Cách tính điểm
- Điểm tổng kết: `Điểm = Tiền tích lũy (nghìn VNĐ) + Uy tín (sao) × 100`.
- Ca ngày (Gather): Thu hoạch bông súng, điên điển, cá linh, cá lóc mang về bến bảo toàn nguyên liệu cho ca tối.
- Ca tối (Quán): Khách vào bàn, gọi món ngẫu nhiên theo kho khả dụng, tính tiền + tip 20% khi phục vụ nhanh, trừ 0.5 uy tín nếu khách bỏ về.

## Sáng tạo của nhóm
- **Đề tài miền Tây trong client (`chonoi/web/index.html`, theo PRD mục 3):** ánh hồng buổi sớm + quầng mặt trời, nước phù sa 2 lớp, sóng lăn tăn + tia sáng dưới nước, bờ dừa nước + nhà sàn cạnh bến; buổi tối có đèn dây vàng nhấp nháy, khói bếp khi nấu, sàn ván + phao nổi của nhà bè trên nước đêm. Út Sen mặc áo bà ba, quấn khăn rằn, đeo kính lặn khi lặn và giỏ lưới đeo hông.
- **Vector hình theo loại nguyên liệu:** cá lóc (sọc, mõm nhọn), cá linh (bạc, đuôi chẻ), cá kèo (dẹt, sọc dọc), bông điên điển (chùm cầu vàng), bông súng (cánh hồng xòe), kèo nèo (chùm hoa); Cá Sấu vẽ riêng kèm cảnh báo "Thủy quái!" viền tím khi tới gần.
- **HUD & màn hình chuẩn Phase 2:** chữ không chân ≥18px @1280×720, giờ đổi màu khi còn ≤30s, checklist "Má Tư cần" (đã lấy/cần từ event `day_plan`), gợi ý hái/cập bến khi tới gần, "Hết hơi!" khi oxy cạn; Menu chính, DayIntro, EveningIntro, DayResult, Shop (mua nâng cấp phím 1/2), Pause (Esc/P) và Summary — tất cả render phòng thủ, sim bật pha nào client hiện pha đó.
- **Thoại giọng Nam Bộ theo event + SFX WebAudio** (không dùng file ngoài, âm lượng nhỏ, mở AudioContext sau phím đầu tiên): ví dụ "Trúng đàn cá linh rồi nè!", "Thu 60k, khách boa nha!" hiện cạnh log kỹ thuật.
- **Bảo toàn Test Contract:** toàn bộ ở tầng presentation (canvas), `chonoi/sim/` và headless độc lập hoàn toàn. Bằng chứng: 2 lần `python -m chonoi.headless --mode gather --seed 1 --ticks 600` cho JSONL **giống nhau từng byte** (`fc /b`: no differences encountered); bộ 57 tests chạy OK trước và sau khi thêm UI.


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
