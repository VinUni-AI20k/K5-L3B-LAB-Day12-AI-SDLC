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

Cần Python 3 trên macOS hoặc Linux. Mở địa chỉ được in trong terminal để chơi.

```bash
git clone '<URL fork của nhóm>' cho-noi && cd cho-noi
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 -m chonoi.live --mode gather --inventory-out catch.json
```

Để chơi **Mở Quán** độc lập, chạy lệnh dưới đây ở thư mục repo. Có thể chạy song song với Gather vì hai ca dùng cổng khác nhau. Thay đường dẫn kho mẫu bằng `catch.json` để dùng nguyên liệu của chính ca Gather vừa kết thúc.

```bash
python3 -m chonoi.live --mode quan --port 8001 --inventory docs/contracts/inventory.sample.json
```

**Điều khiển** — WASD hoặc phím mũi tên để bơi hoặc đi. `E` để hái, cập bến hoặc tương tác với bếp/bàn. `Space` để bắt cá khi lặn. `R` để chơi lại.

**Điểm Phase 1** — Tổng tiền kiếm được (nghìn đồng) cộng `100 × floor(uy tín)`. Uy tín được làm tròn xuống trước khi nhân.

Game cần chế độ **headless** theo Test Contract (`python3 -m chonoi.headless --mode gather|quan …`) để được chạy và chấm tự động. **Công nghệ không ràng buộc**: khung Python trong `chonoi/` chỉ là gợi ý, chi tiết ở [`docs/STARTER.md`](docs/STARTER.md).

## Bàn giao kho Phase 1

File kho có duy nhất khóa `items`, ánh xạ bốn ID nguyên liệu hợp lệ (`ca_loc`, `ca_linh`, `bong_sung`, `bong_dien_dien`) tới số nguyên không âm. Khóa vắng tính là 0 và bên ghi bỏ các mục bằng 0. Kho rỗng là `{"items":{}}`. Schema và thời điểm ghi theo [PRD-0 mục G](PHASE1.md#g-file-kho-hợp-đồng-tích-hợp-lặn--hái--mở-quán).

```json
{"items":{"bong_sung":2,"ca_loc":1}}
```

`gather --inventory-out` ghi kho một lần khi có `gather_end`. `quan --inventory` đọc file này ở tiến trình riêng. Khi cần phát triển Quán độc lập, dùng [kho mẫu](docs/contracts/inventory.sample.json). Xem [kế hoạch chia việc](docs/plan/phase-1.md) và [giao diện tích hợp](docs/plan/phase-1-integration.md).

Phase 2 giữ schema này, thêm hai ID nguyên liệu `ca_keo` và `keo_neo`, và bổ sung chế độ `day` bàn giao kho trong bộ nhớ. Xem [kế hoạch Phase 2](docs/plan/phase-2.md) và [giao diện Test Contract v1.1](docs/plan/phase-2-integration.md).

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
