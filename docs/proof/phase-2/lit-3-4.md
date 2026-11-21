# Bằng chứng lát 3–4 — quán và vòng ngày

- Lát 3: `QuanSim` lọc món gọi theo `day_plan`; dữ liệu 2 bếp, 4 bàn, 6 món và D1–D5 giữ trong `game.contract.json`.
- Lát 4: `DaySim` điều phối gather → quán → Shop, bàn giao kho cá thể v1.2, chuyển pha cùng tick, giữ tiền/uy tín/nâng cấp, làm mới giỏ, hồi oxy/Máu và xóa timer tạm đầu ngày; Shop xử lý `buy` trước `shop_done`/timeout.
- `Session` quản lý tick mô phỏng, phase_tick, pause/resume và output day; headless/live nhận mode `day`.

