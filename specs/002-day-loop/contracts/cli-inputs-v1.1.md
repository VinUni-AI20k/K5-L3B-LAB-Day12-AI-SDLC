# CLI, inputs, scenario v1.1

```
python3 -m chonoi.headless --mode gather|quan|day --seed N --ticks N --out F
    [--scenario F] [--inputs F] [--inventory F (quan)] [--inventory-out F (gather)]
    [--days N (day, 1–5, mặc định 1)] [--snapshot-every N]
```
- `--days` khác `day` hoặc ngoài 1–5 → mã 2. `--inventory*` với `day` → mã 2 (GIẢ ĐỊNH).

## Inputs (frame)
`tick, move, interact, catch` (v1.0) + `pause` (bool, mọi mode), `shop_done` (bool, Shop), `buy` (chuỗi khác rỗng: `"oxygen"`, `"hp"`; chỉ tại frame khai báo, không kế thừa; chuỗi không hỗ trợ → `buy_failed unknown`). `attack`/`photo` chưa bật → GIẢ ĐỊNH mã 2 (trường lạ). Cạnh lên cho bool; giữ nút qua đổi pha không tạo cạnh mới. Mở rộng: `attack`, `photo`, `buy:<kind>`/`sell:<kind>`.

## Scenario `day`
```json
{"day":{"money":200,"earned":200},"gather":{"hold":["ca_loc","bong_sung","bong_sung"],"random_fish":false}}
```
- `0 ≤ money ≤ earned` (khai cả hai khi có tiền). `day.day_plan` ghi đè theo `day`, tính lại `ingredients` và so nếu khai.
- Cấm `quan.stock`, `quan.reputation` trong `day`. `gather`/`quan` là mẫu khởi tạo mỗi Ngày.
- `gather.fish[].age_ticks` (mặc định 0); `gather.monsters[] {id,kind,pos,waypoints,target_idx(=1),state(=patrol),state_ticks_left,recoil_dir(null)}`; `gather.player.invuln_ticks`.
