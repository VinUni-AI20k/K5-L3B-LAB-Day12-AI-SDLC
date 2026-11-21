# Demo 3 phút — Quán Ăn Chợ Nổi (MMMV)

Chuẩn bị: `python3 -m chonoi.live --mode gather` mở sẵn ở tab 1, `python3 -m chonoi.live --mode quan` ở tab 2, terminal ở tab 3.

## 0:00 – 0:25 Mở đầu

Nói một câu: Út Sen lặn hái buổi sáng, tối nấu bán trên nhà bè; hai buổi nối nhau bằng file kho. Không dựng slide.

Màn hình: tab 1, HUD sáng — thời gian, oxy, Máu, giỏ.

## 0:25 – 1:10 Buổi sáng

Bơi sang nút bông súng, bấm `E` khi prompt hiện; chỉ ra giỏ tăng 1 ô.

Lặn xuống: thanh oxy tụt, `d` hiện trên HUD. Bấm `Space` cạnh đàn cá — đàn biến mất, giỏ tăng 3 con cá linh.

Nếu muốn cho thấy nguy hiểm: lặn xuống `d ≥ 10` gần Cá Sấu, để nó đuổi, bị cắn một lần — mất 1 Máu, rơi nửa giỏ.

Nhấn mạnh: cùng seed, hai lần chạy ra cùng file JSONL.

## 1:10 – 1:30 Bàn giao

Bơi về bến, `E`. Buổi sáng kết thúc, kho ghi ra file. Chuyển tab 2 với `--inventory`.

## 1:30 – 2:20 Buổi tối

Khách vào bàn T1. Đi tới bếp `B1`, `E` để nấu — bếp hiện đếm ngược. Chín thì `E` bưng, sang bàn `E` phục vụ. Khách ăn xong trả tiền, uy tín tăng nếu kịp.

Cho xem một khách bỏ đi vì chờ lâu: uy tín giảm 0,5.

## 2:20 – 2:45 Vòng ngày (backend)

Tab 3: `python3 -m chonoi.headless --mode day --days 2 --seed 7 --out day.jsonl`. Mở file, chỉ `day_start`, `day_plan` (món Má Tư giao), `phase_start`, rồi `shop_end`. Nói rõ: HUD vòng ngày còn đang làm, hiện chạy được ở headless.

## 2:45 – 3:00 Kiểm chứng

`python3 tools/run_checks.py` — bốn cổng: test, smoke hai tiến trình, tất định từng byte, bằng chứng dẫn đúng.

Mở `docs/verification/phase-1.md`, chỉ một dòng AC và file proof tương ứng. Kết thúc ở đó, đừng kể thêm.
