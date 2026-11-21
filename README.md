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
git clone https://github.com/miao1114/K5-L3B-LAB-Day12-AI-SDLC-CodexGemini.git
cd K5-L3B-LAB-Day12-AI-SDLC-CodexGemini
python3 -m chonoi.live --mode gather
```

Mở địa chỉ localhost được in ra để chơi. Đổi `--mode gather` thành `--mode quan` để chơi buổi tối riêng. Chạy toàn bộ test suite bằng **một lệnh** từ gốc repo:

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```

Trạng thái kiểm chứng Phase 1 hiện tại: 46/47 test đạt; test ngất còn chờ tích hợp Lát 1 (xem [`docs/verification/phase-1.md`](docs/verification/phase-1.md)). Game cần chế độ **headless** theo Test Contract (`python3 -m chonoi.headless --mode gather|quan …`) để được chạy và chấm tự động. **Công nghệ không ràng buộc**: khung Python trong `chonoi/` chỉ là gợi ý, chi tiết ở [`docs/STARTER.md`](docs/STARTER.md).

### Buổi sáng — Gather

Út Sen bơi trong mặt cắt sông `[x, d]`, với `d` tăng khi lặn xuống. Dùng **WASD** hoặc **phím mũi tên** để di chuyển; bơi lên mặt nước để hồi oxy, lặn xuống thì oxy giảm. Út Sen có 3 Máu và mất Máu khi ngạt. **E** tương tác với nút bông điên điển/bông súng ở mặt nước hoặc cập bến; **Space** bắt đàn cá khi ở dưới nước; **R** chơi lại. Giỏ chứa tối đa **12 ô**, mỗi nguyên liệu chiếm một ô; cá linh cho 3 con, cá lóc cho 1 con. Giỏ thiếu chỗ thì không lấy lẻ. Cập bến hoặc hết giờ giữ nguyên hàng trong giỏ để chuyển sang quán; ngất thì mất toàn bộ giỏ và kho bàn giao rỗng.

### Hợp đồng file kho (`inventory`)

Hai buổi có thể chạy bằng hai tiến trình headless: `gather --inventory-out kho.json` ghi kho khi có `gather_end`, rồi `quan --inventory kho.json` đọc cùng file. File JSON chỉ có khóa gốc `items`; mỗi khóa con là một trong `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`, giá trị là số nguyên không âm. Loại vắng mặt tính là 0; bên ghi bỏ khóa có lượng 0. Ví dụ hợp lệ:

```json
{"items":{"bong_sung":2,"ca_loc":1}}
```

Kho rỗng là `{"items":{}}`. Nếu Gather kết thúc do ngất thì ghi kho rỗng. Nếu chỉ dừng vì giới hạn `--ticks` trước khi kết thúc buổi sáng thì không tạo hoặc ghi đè file kho. Khi có `gather_end`, nội dung file phải khớp `gather_end.inventory` và được ghi bằng cách thay thế nguyên tử. Quán từ chối file sai schema hoặc nguyên liệu lạ (mã thoát 2).

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
