# Research Phase 2 — Test Contract v1.1, vòng ngày, ảnh hưởng code

> Người viết: worker RESEARCH (Claude), chỉ đọc code. Ngày 2026-11-21, branch `tv6/phase-1-team-ai`, HEAD `8f4330e`.
> Nguồn: `docs/prd/phase-2-ticket-02.md` (TICKET-02, bản text thô). **Cập nhật**: đề đã được chép lại đầy đủ (535 dòng); số dòng `:N` ở mục 1.1 và 2.2 theo bản cũ, còn mục 7 dẫn theo **bản mới**. Các chỗ `[CẮT]` cũ đã được thay bằng giá trị trong đề, chỉ còn lại những chỗ vẫn thiếu. Chỗ suy luận ghi **GIẢ ĐỊNH**.
> Số dòng `chonoi/` theo working tree lúc viết. `chonoi/sim/gather.py` đang có lát 1 đã stage nhưng chưa commit; file có thể đổi tiếp.

## 0. Hiện trạng (đo lúc viết)

| Mục | Trạng thái |
|---|---|
| Test | `PYTHONPATH=tests:. python3 -m unittest discover -s tests` → **32 test, OK** |
| Luật P1 | Lát 1 (oxy, ngạt, ngất, giỏ) có trong working tree (`gather.py:145-174`, `try_add_hold` `:131-141`). **Lát 2 (hái, bắt cá) và toàn bộ quán (lát 3–4) vẫn là TODO** (`gather.py:120,124`, `quan.py:40,75,77,78`) |
| Tag | Chưa có tag `phase-1` (`git tag` rỗng) |
| Contract | `game.contract.json` vẫn là v1.0, `team_size: 4` |
| Hiệu năng | Gather 22.200 tick (đi chéo, ngất ở tick 1992): **0,09 s**; `--snapshot-every 1`: 0,17 s. Ngân sách 20 s còn dư rất nhiều |

Hệ quả: test ẩn P2 **kiểm lại P1 với số chuẩn**. Lát 2–4 của P1 phải xong trước, nếu không mọi test P1 về hái, bắt cá, quán đều trượt ở cả phase 2.

Lát 1 đã khớp đề: ngạt "tính cả bước vừa chạm 0" và "reset khi oxy > 0 hoặc lên mặt nước" (`gather.py:158-164`).

---

## 1. Diff contract v1.0 → v1.1

### 1.1 Bảng khóa thêm/đổi

| Đường dẫn | v1.0 hiện tại | v1.1 chuẩn | Nguồn (dòng PRD) |
|---|---|---|---|
| `contract_version` | `"1.0"` | `"1.1"` (bản mới `:268`, `:518`) | §4.1 |
| `extensions` (gốc manifest) | — | mảng mã mở rộng nhóm làm, vd. `[]` hoặc `["burn"]` (**GIẢ ĐỊNH** dạng mảng) | §3 `:298-300` |
| `team_size` | 4 | số người thật (TEAM.md có 6) | README |
| `gather.fish_yield` | linh 3, lóc 1 | + `ca_keo: 2` | §1.1 `:58` |
| `gather.nodes` | N1–N4 | + `N5 keo_neo [76,0]`, `N6 keo_neo [90,0]` | `:47` |
| `gather.fish_initial` | **mảng 6 đàn** | **số `8`** (số đàn đầu ca, vị trí theo seed) | §4.1 `:381` |
| `gather.fish_speed` | — | `1.5` (m/s) | `:62` |
| `gather.fish_turn_ticks` | — | `120` (đổi hướng ở bước bơi 120, 240…) | `:62` |
| `gather.fish_max` | — | `12` | `:77` |
| `gather.fish_spawn_ticks` | — | `360` (sinh tại `phase_tick = 360·k`, k ≥ 1) | `:77` |
| `gather.fish_spawn_clearance` | — | `1.0` (điểm sinh phải cách mọi đàn **> 1 m**) | `:77` |
| `gather.fish_x` | — | `[4, 96]` (miền bơi x) | `:62` |
| `gather.fish_depths` | — | map loài → miền d: linh `[3,12]`, lóc `[8,20]`, kèo `[22,28]` | `:62` |
| `gather.fish_spawn_x` | — | `[15,30,45,60,75,90]` | `:67` |
| `gather.fish_spawn_depths` | — | linh `[5,10]`, lóc `[10,16]`, kèo `[24,27]` | `:67` |
| `gather.fish_weights` | — | linh 0.4, lóc 0.3, kèo 0.3 | `:77` |
| `gather.monsters` | — | `species.ca_sau{…}`, `spawns[]`, `invuln_ticks: 90`, `loss_ratio: 0.5` | §1.2, §4.1 `:393` |
| `quan.stoves` | B1 | + `B2 [5,8]` | `:130` |
| `quan.tables` | T1 | + `T2 [13,2]`, `T3 [9,6]`, `T4 [13,6]` | `:134` |
| `menu` | 3 món | + `canh_chua_ca_loc`, `ca_keo_nuong`, `lau_mam` | `:164-212` |
| `day_plan` | — | mảng 5 `{day, dishes, ingredients}` | §2, §4.1 `:402` |
| `shop` | — | `{max_ticks: 600, upgrades:{oxygen[], hp[]}}` | §2 `:260-281`, §4.1 `:410` |

Số khác giữ nguyên như v1.0 (đề §1 khớp từng số: bounds, bến, bơi 4.0, ramp 6, oxy 30 s, refill 6, choke 60, hp 3, giỏ 12, hái 2.0, regrow 20 s, catch 2.0, cooldown 0.5 s, quán 180 s, đi 4.0, interact 1.5, khách 120 + 900·k, kiên nhẫn 60 s, ăn 10 s, boa 0.2, ngưỡng 0.5, +0.2, −0.5, uy tín 3.0 trong [0,5], `burn_s: null`, điểm ×100).

### 1.2 Chỗ chưa rõ trong contract
- `ca_keo_nuong`: nấu **6 s**, giá 70 (bản mới `:133-137`). Đã điền vào JSON.
- `recoil_dist`: đề ghi "mỗi bước 2/60 m" trong 60 bước → tổng **2.0 m**. GIẢ ĐỊNH `recoil_dist` là tổng quãng (2.0), không phải m/s.
- Ngưỡng độ sâu để Cá Sấu phát hiện (`d ≥ 10`) trùng `depths[0]`. Mở rộng rắn cũng vậy (`depths [8,20]`, rời chase khi `d < 8`). → dùng `species.depths[0]` làm ngưỡng, không thêm khóa.
- Vị trí `day_plan` và `shop`: GIẢ ĐỊNH nằm trong `tuning` (cạnh `gather`/`quan`/`menu`).

### 1.3 Ingredients đã tính sẵn (khớp bảng đề `:227-259`)

| Ngày | dishes | ingredients | Số ô | Ô thực tế (bắt theo đàn) |
|---|---|---|---|---|
| 1 | ca_loc_nuong_trui 3, goi_bong_sung 3 | bong_sung 6, ca_loc 3 | 9 | 9 |
| 2 | ca_loc_nuong_trui 2, lau_ca_linh_dien_dien 2 | bong_dien_dien 2, ca_linh 6, ca_loc 2 | 10 | 10 |
| 3 | goi_bong_sung 2, canh_chua_ca_loc 2, ca_keo_nuong 2 | bong_dien_dien 2, bong_sung 4, ca_keo 4, ca_loc 2 | 12 | 12 |
| 4 | lau_mam 1, ca_loc_nuong_trui 2, goi_bong_sung 1 | bong_dien_dien 1, bong_sung 2, ca_keo 1, ca_linh 2, ca_loc 2, keo_neo 1 | 9 | 11 |
| 5 | lau_mam 1, lau_ca_linh_dien_dien 1, ca_loc_nuong_trui 1 | bong_dien_dien 2, ca_keo 1, ca_linh 5, ca_loc 1, keo_neo 1 | 10 | 12 |

Đã tính bằng script (tổng công thức × số suất), cả 5 dòng khớp đề.

### 1.4 JSON đề xuất để TV1 dán (thay khối `tuning` và đầu file)

```json
{
  "contract_version": "1.1",
  "team": "ten-nhom",
  "team_size": 6,
  "extensions": [],
  "build_cmd": "true",
  "run_cmd": "python3 -m chonoi.live --mode gather",
  "headless_cmd": "python3 -m chonoi.headless",
  "tuning": {
    "tick_hz": 60,
    "gather": {
      "duration_s": 180,
      "bounds": {"x": [0, 100], "d": [0, 30]},
      "dock_pos": [2, 0],
      "dock_radius": 3,
      "start_pos": [2, 0],
      "start_heading_deg": 0,
      "swim_speed": 4.0,
      "ramp_max_ticks": 6,
      "surface_depth": 0.5,
      "oxygen_max_s": 30,
      "oxygen_refill_per_tick": 6,
      "choke_interval_ticks": 60,
      "hp_max": 3,
      "hold_capacity": 12,
      "interact_radius": 2.0,
      "node_yield": 1,
      "regrow_s": 20,
      "catch_radius": 2.0,
      "catch_cooldown_s": 0.5,
      "fish_yield": {"ca_linh": 3, "ca_loc": 1, "ca_keo": 2},
      "nodes": [
        {"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]},
        {"id": "N2", "kind": "bong_dien_dien", "pos": [28, 0]},
        {"id": "N3", "kind": "bong_sung", "pos": [44, 0]},
        {"id": "N4", "kind": "bong_sung", "pos": [60, 0]},
        {"id": "N5", "kind": "keo_neo", "pos": [76, 0]},
        {"id": "N6", "kind": "keo_neo", "pos": [90, 0]}
      ],
      "fish_initial": 8,
      "fish_speed": 1.5,
      "fish_turn_ticks": 120,
      "fish_max": 12,
      "fish_spawn_ticks": 360,
      "fish_spawn_clearance": 1.0,
      "fish_x": [4, 96],
      "fish_depths": {"ca_linh": [3, 12], "ca_loc": [8, 20], "ca_keo": [22, 28]},
      "fish_spawn_x": [15, 30, 45, 60, 75, 90],
      "fish_spawn_depths": {"ca_linh": [5, 10], "ca_loc": [10, 16], "ca_keo": [24, 27]},
      "fish_weights": {"ca_linh": 0.4, "ca_loc": 0.3, "ca_keo": 0.3},
      "monsters": {
        "species": {
          "ca_sau": {"patrol_speed": 1.0, "chase_speed": 3.0, "detect_radius": 10, "exit_radius": 16,
                     "depths": [10, 30], "hit_radius": 1.5, "recoil_ticks": 60, "recoil_dist": 2.0}
        },
        "spawns": [
          {"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]], "from_day": 1},
          {"id": "M2", "kind": "ca_sau", "pos": [85, 18], "waypoints": [[85, 18], [89, 18]], "from_day": 3}
        ],
        "invuln_ticks": 90,
        "loss_ratio": 0.5
      }
    },
    "quan": {
      "duration_s": 180,
      "bounds": {"x": [0, 16], "z": [0, 10]},
      "start_pos": [8, 5],
      "walk_speed": 4.0,
      "ramp_max_ticks": 6,
      "interact_radius": 1.5,
      "stoves": [{"id": "B1", "pos": [2, 8]}, {"id": "B2", "pos": [5, 8]}],
      "tables": [{"id": "T1", "pos": [9, 2]}, {"id": "T2", "pos": [13, 2]},
                 {"id": "T3", "pos": [9, 6]}, {"id": "T4", "pos": [13, 6]}],
      "first_customer_tick": 120,
      "customer_interval_s": 15,
      "patience_s": 60,
      "eat_s": 10,
      "burn_s": null,
      "carry_limit": 1,
      "tip_rate": 0.2,
      "tip_min_patience_ratio": 0.5,
      "tip_reputation": 0.2,
      "left_reputation_delta": -0.5,
      "reputation_initial": 3.0,
      "reputation_min": 0,
      "reputation_max": 5
    },
    "menu": {
      "ca_loc_nuong_trui": {"recipe": {"ca_loc": 1}, "cook_s": 6, "price": 60},
      "goi_bong_sung": {"recipe": {"bong_sung": 2}, "cook_s": 4, "price": 40},
      "lau_ca_linh_dien_dien": {"recipe": {"ca_linh": 3, "bong_dien_dien": 1}, "cook_s": 10, "price": 120},
      "canh_chua_ca_loc": {"recipe": {"ca_loc": 1, "bong_dien_dien": 1}, "cook_s": 8, "price": 90},
      "ca_keo_nuong": {"recipe": {"ca_keo": 2}, "cook_s": 6, "price": 70},
      "lau_mam": {"recipe": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}, "cook_s": 12, "price": 200}
    },
    "day_plan": [
      {"day": 1, "dishes": {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3},
       "ingredients": {"bong_sung": 6, "ca_loc": 3}},
      {"day": 2, "dishes": {"ca_loc_nuong_trui": 2, "lau_ca_linh_dien_dien": 2},
       "ingredients": {"bong_dien_dien": 2, "ca_linh": 6, "ca_loc": 2}},
      {"day": 3, "dishes": {"ca_keo_nuong": 2, "canh_chua_ca_loc": 2, "goi_bong_sung": 2},
       "ingredients": {"bong_dien_dien": 2, "bong_sung": 4, "ca_keo": 4, "ca_loc": 2}},
      {"day": 4, "dishes": {"ca_loc_nuong_trui": 2, "goi_bong_sung": 1, "lau_mam": 1},
       "ingredients": {"bong_dien_dien": 1, "bong_sung": 2, "ca_keo": 1, "ca_linh": 2, "ca_loc": 2, "keo_neo": 1}},
      {"day": 5, "dishes": {"ca_loc_nuong_trui": 1, "lau_ca_linh_dien_dien": 1, "lau_mam": 1},
       "ingredients": {"bong_dien_dien": 2, "ca_keo": 1, "ca_linh": 5, "ca_loc": 1, "keo_neo": 1}}
    ],
    "shop": {
      "max_ticks": 600,
      "upgrades": {
        "oxygen": [{"level": 1, "price": 200, "oxygen_max_s": 45}, {"level": 2, "price": 400, "oxygen_max_s": 60}],
        "hp": [{"level": 1, "price": 250, "hp_max": 4}, {"level": 2, "price": 500, "hp_max": 5}]
      }
    },
    "score": {"reputation_multiplier": 100}
  }
}
```

**Cảnh báo**: dán JSON này sẽ làm `contract.py` hiện tại **báo mã 2 cho mọi lệnh**, vì nó buộc `fish_initial` là mảng 6 (`contract.py:97-99`) và chỉ nhận 2 loại nút (`:89-96`). Phải sửa `contract.py` cùng commit (mục 3).

---

## 2. Sự kiện mới và thứ tự xử lý

### 2.1 Sự kiện v1.1 (§4.4 `:540-615`)

| Sự kiện | Pha | `data` | Ghi chú |
|---|---|---|---|
| `monster_hit` | gather | `{monster_id, hp, lost, pos}` | `pos` = vị trí **người chơi**; `lost` = mảng kind theo LIFO (mất trước đứng trước) |
| `fish_spawned` | gather | `{id, kind, pos}` | chỉ khi sinh theo lịch (không phát cho 8 đàn đầu ca) |
| `faint` | gather | Do bị chạm: `{"cause":"monster","lost":[…phần giỏ còn lại…],"hp":0}` (bản mới `:416`) | Do ngạt: đề không nói → GIẢ ĐỊNH giữ `{}` như v1.0 (P2-Q3) |
| `day_start` | day | `{}` (bản mới `:417-418`); số Ngày nằm ở trường `day` của vỏ event | |
| `phase_start` | day | `{}` | pha mới nằm ở trường `phase` của vỏ event |
| `day_plan` | day | `{dishes, ingredients}` của Ngày đó | |
| `paused`, `resumed` | mọi mode | `{}` (GIẢ ĐỊNH, ô bảng gộp) | |
| `bought` | shop | `{upgrade, level, price, money}` | `money` sau khi trừ |
| `buy_failed` | shop | `{action, reason}`; reason ∈ `funds`, `max_level`, `out_of_stock`, `unknown` | `action` = chuỗi `buy` gốc |
| `shop_end` | shop | `{reason: "done"\|"time"}` | |
| Mở rộng | | `attack{pos,monster_ids}`, `monster_stunned{monster_id,pos,stun_ticks}`, `photo{id,reputation}`, `released{id}`, `dish_burnt{stove_id,order_id,dish_id,order_status}`, `vendor_trade{action,kind,price,money}` | chỉ khi bật |

- Vỏ event ở mode `day` có thêm trường `day`. Ví dụ trong đề (bản mới `:436`): `{"type":"event","tick":0,"phase":"gather","day":1,"name":"day_plan","data":{"dishes":{…},"ingredients":{…}}}`. Thứ tự khóa: `type, tick, phase, day, name, data`.
- "Event kết thúc mang pha cũ" (`:538`): `gather_end` có `phase:"gather"`, kể cả khi `phase_start(quan)` phát cùng tick.
- Dòng `end` của `day` thêm `days_completed` (số Shop đã đóng). Đủ Ngày thì `reason: "days_complete"` (bản mới `:440-442`).

### 2.2 Thứ tự một bước

**Gather (§4.5 `:617-623`)**
1. Đồng hồ, cooldown, giảm `invuln_ticks`, hồi nút (`node_regrown`).
2. Bơi → `dive`/`surface` → oxy → ngạt (`choke`). Máu 0 → `faint` → `gather_end(fainted)`, bỏ các bước còn lại.
3. (Lao, nếu bật.)
4. Cập nhật quái **theo id** (patrol/chase/recoil) → xét **tối đa một** hit (con gần nhất, hòa theo id). Máu 0 → `faint` → `gather_end(fainted)`.
5. `interact`: bến trước, rồi hái.
6. `catch`: dùng vị trí cá **trước khi cá bơi** tick này; rồi ảnh (nếu bật).
7. Hết giờ → `gather_end(time)`.
8. Nếu còn giờ: cá bơi → sinh theo lịch (`fish_spawned`) → Cá Hô (nếu bật).

Hệ quả: cùng tick có thể có `choke` rồi `monster_hit`; cập bến thắng bắt cá và hết giờ nếu còn Máu. Code hiện tại (`gather.py:99-128`) đã đúng thứ tự 1–2–5–6–7; cần chèn bước 4 giữa oxy và interact, thêm bước 8 sau hết giờ.

**Cá bơi (`:62`, `:77`)**: 1.5 m/s = 0.025 m/tick. Ở bước bơi thứ 120, 240… (theo `age_ticks` của đàn) đổi hướng theo seed **trước** khi di chuyển. Chạm mép miền (`fish_x` × `fish_depths[loài]`) thì phản xạ phần quãng còn lại và đảo thành phần hướng vuông góc với mép đó (chạm góc đảo cả hai). Sinh: tại `phase_tick % 360 == 0` (k ≥ 1), sau khi cá bơi, nếu số đàn < 12 và còn điểm hợp lệ (cách mọi đàn đang sống **> 1 m**). Chọn loài theo trọng số chuẩn hóa lại trên các loài còn điểm → chọn đều một điểm → hướng theo seed. Cá mới bơi từ bước sau (age 0).

**Cá Sấu (§1.2 `:89-120`)**
- `patrol` 1.0 m/s tới waypoint; đến nơi thì đổi mục tiêu cho bước sau. `target_idx` mặc định 1 (waypoint 0 là chỗ xuất phát).
- `patrol → chase` khi người chơi ở `d ≥ 10` và cách ≤ 10 m; `chase` 3.0 m/s về phía người chơi. `chase → patrol` khi cách > 16 m hoặc người chơi lên `d < 10` (bản mới `:62-68`).
- Kẹp theo biên map và `depths` của loài.
- Hit: sau khi cả hai di chuyển, cách ≤ 1.5 m, người chơi ở `[VẪN THIẾU trong đề, bản mới :70-71]` (GIẢ ĐỊNH: dưới nước, P2-Q7) và `invuln_ticks == 0` → −1 Máu, bỏ `floor(len(hold) × 0.5)` món từ cuối giỏ, `invuln = 90`. Không đổi sang recoil trong lúc người chơi bất tử.
- `recoil` 60 bước, **bắt đầu từ bước sau**: lùi theo hướng xa người chơi chốt lúc chạm (trùng tâm thì +x), mỗi bước 2/60 m trước khi chặn mép, không gây hit. Hết recoil về patrol, xét phát hiện/chạm từ bước kế.
- M2 chỉ có từ Ngày 3. `gather` độc lập dùng bố trí Ngày 1 (chỉ M1).
- Ngạt **xuyên bất tử** và không làm rơi hàng (`:43`).

**Quán (§4.5 `:624-626`)**: giữ thứ tự v1.0. Trong `day`: lọc menu theo id món trong kế hoạch **trước**, rồi lọc nguyên liệu khả dụng (kho − phần đang giữ); khách chọn **đều theo seed**. Quán độc lập dùng cả 6 món. Có bàn trống mà không món nào nấu được → `no_dish`. Bếp lấy đơn `reserved` cũ nhất theo `order_tick` rồi id bàn. Đóng ca: khách đang ăn trả tiền ngay, khách đang chờ rời đi **không trừ uy tín**, dọn món và phần giữ.

**Đổi pha (`:627-637`)**
- Đầu Ngày: `day_start` → `day_plan` → `phase_start(gather)`.
- `gather_end` → dựng quán (kho = giỏ bàn giao, rỗng nếu ngất) → `phase_start(quan)` **cùng tick**.
- `quan_end` → dựng Shop → `phase_start(shop)` cùng tick.
- Pha mới chỉ chạy gameplay **từ bước sau**. Snapshot đổi pha ghi pha mới với `phase_tick: 0`.
- Các màn DayIntro/EveningIntro/DayResult/Summary **không tốn tick headless**: 10.800 + 10.800 + 600 = 22.200 đúng bằng trần một Ngày (`:226`). Chúng chỉ là UI.

**Shop (`:638-647`)**
- Mỗi bước: xử lý một `buy` (nếu frame có) **trước** cạnh `shop_done`, kể cả ở bước cuối.
- `shop_done` → `shop_end(done)`; hết 600 tick hoạt động → `shop_end(time)`.
- Đóng Shop → `days_completed += 1` → kết thúc (đủ `--days`) hoặc dựng Ngày kế **ngay tick đó**.
- Chỉ khi dựng Ngày mới mới chép `upgrades` → `active_upgrades`. Oxy/Máu đầy theo cấp đang áp dụng, giỏ mới, kho dư bị bỏ.
- Mua: đủ đúng giá là mua được; mỗi lần mua cấp kế tiếp. Trừ `money`, **giữ `earned`** và điểm. Không đủ tiền → `buy_failed(funds)`; đã tối đa → `max_level`; lệnh lạ → `unknown`.

**Pause (§4.2 `:445-455`)**
- Xét cạnh `pause` **trước** mọi thứ.
- Vào pause: chỉ tăng `tick` ngoài, phát `paused`. Đang pause: bỏ qua cạnh hành động; `sim_tick`, `phase_tick`, lịch, timer đứng yên.
- Cạnh `pause` tiếp theo: phát `resumed` **và chạy gameplay ngay bước đó**.
- Giữ nút qua đổi pha không tạo cạnh mới.

---

## 3. Bản đồ ảnh hưởng

Ký hiệu: **K** = file khung (luật chung cấm sửa → **cần nhóm/integrator quyết**), **N** = file của nhóm.

| Yêu cầu | File / hàm | Loại | Việc |
|---|---|---|---|
| `--mode day`, `--days 1..5` | `chonoi/headless.py:36-48` | **K** | Bỏ chặn `day` (`:47-48`); thêm `--days` (chỉ với day, 1–5, mặc định 1; sai → mã 2) |
| Nút `pause`, `shop_done` (bool), `buy` (chuỗi, chỉ ở frame khai báo) | `chonoi/inputs.py:13,26-61,72-91` | **K** | `BUTTONS_V10` → thêm `pause`, `shop_done`; `load_frames` nhận `buy` là chuỗi khác rỗng; `InputPlayer.advance` trả `buy` **không kế thừa**; `InputState` thêm `buy` |
| Nút mở rộng `attack`/`photo` | `inputs.py` | **K** | Chỉ khi bật. Không bật thì **bỏ qua** (mã 0), nên test P1 `test_smoke_p1.py:65-67` đòi mã 2 phải sửa (mục 4.1) |
| 6 nguyên liệu | `chonoi/inventory.py:13` (`KINDS_P1`) | **K** | + `ca_keo`, `keo_neo`, nếu không file kho có `ca_keo` → mã 2 |
| Scenario v1.1 | `chonoi/scenario.py:13-20, 43-46, 84-163` | **K** | `GATHER_KEYS` + `monsters`, (`ca_ho`, `random_ho`); `NODE_KINDS`/`FISH_KINDS` thêm loài mới; `fish[].age_ticks`; `monsters[]` `{id,kind,pos,waypoints,target_idx,state,state_ticks_left,recoil_dir}`; khối `day{money,earned,reputation,upgrades,day_plan}`; mode day nhận nhiều khối (`:45-46` hiện cấm); cấm `quan.stock`/`quan.reputation` khi chạy day; `0 ≤ money ≤ earned` |
| Kiểm tuning v1.1 | `chonoi/contract.py:76-110,140-143` | **K** | `fish_initial` là số; 3 loại nút, 3 loài cá; kiểm khóa cá/quái/shop/day_plan; tính lại `ingredients` và so |
| Session nhiều pha, 3 bộ đếm tick | `chonoi/runner.py:21-25,28-35,51-69,77-97` | **K** | `build_sim` cho `day`; `_common` hiện gán `tick = sim_tick = phase_tick` (`:52`) → cần tách 3 bộ đếm (pause, đổi pha); `state` thêm giá trị `"paused"` (bản mới `:380`); vỏ event thêm `day`; `end_row` thêm `days_completed`; `write_inventory_if_done` không dùng trong day |
| Live cho day + pause/shop | `chonoi/live.py:118-125,218` | **K** | `--mode` thêm `day`; `set_input` nhận `pause`, `shop_done`, `buy`; `meta` theo **pha** hiện tại (`tuning[phase]`) và thêm `menu`, `day_plan`, `shop` |
| Số chuẩn + cá bơi/sinh | `chonoi/sim/gather.py` `__init__` `:57-68`, `step`, thêm `_fish_step`, `_spawn` | N | `fish_initial` số → chọn 8 điểm khác nhau theo seed; bơi/phản xạ/đổi hướng; sinh; `age_ticks` |
| Bắt cá cả đàn | `gather.py` (lát 2) | N | `try_add_hold` thêm **từng món** (`:131-141`) → cần kiểm `len(hold) + yield ≤ 12` **trước**, nếu không sẽ thêm thiếu. Cooldown chỉ đặt khi bắt thành công |
| Cá Sấu, bất tử, rơi hàng | `gather.py` mới `_monsters_step`, `_monster_hit` | N | Chèn giữa oxy và interact; `invuln_ticks` đã có (`:52,103`) |
| HP/oxy theo cấp | `gather.py:48-50` | N | `oxygen_max`/`hp_max` lấy từ `active_upgrades` khi chạy day |
| 2 bếp/4 bàn, 6 món, kế hoạch | `chonoi/sim/quan.py` (lát 3–4 P1 vẫn TODO) | N | Ghế trống id nhỏ nhất; lọc menu theo kế hoạch; `order_tick`; đóng ca |
| Vòng ngày + Shop | **mới** `chonoi/sim/day.py` (`DaySim`), có thể `chonoi/sim/shop.py` | N | Bọc `GatherSim` → `QuanSim` → Shop; giữ `money/earned/reputation/upgrades`; phát sự kiện đổi pha |
| Pause | Đặt ở runner (`Session.step`) hoặc `DaySim` | K hoặc N | Nên đặt trong một lớp bọc sim để gather/quan độc lập cũng có pause (đề: "pause ở cả ba mode") |
| HUD/menu/pause UI | `chonoi/web/index.html` | N (UI) | Mục 5 |
| Test | `tests/` | (QA) | Sửa test P1 có lý do (mục 4) + test mới |

**Đề xuất cho nhóm quyết**: các file **K** (`headless`, `inputs`, `inventory`, `scenario`, `contract`, `runner`, `live`) **bắt buộc phải sửa** để đạt v1.1, không có đường vòng: CLI `--days`, nút `buy` dạng chuỗi và loài `ca_keo` đều bị khung chặn trước khi tới sim. Đề xuất: giao một người (Integrator/TV1) giữ toàn bộ thay đổi khung trong một commit "khung v1.1", các lát khác chỉ sửa `chonoi/sim/`.

---

## 4. Test ẩn và regression

### 4.1 P1 bị kiểm lại với số chuẩn: test hiện có sẽ vỡ hoặc đổi

| Test hiện có | Vì sao vỡ ở v1.1 | Đề xuất (ghi lý do trong commit) |
|---|---|---|
| `test_smoke_p1.py:45` `len(s["fish"]) == 6` | `fish_initial = 8` | Đổi thành 8, đọc từ tuning |
| `test_smoke_p1.py:70-77` `--mode day` → mã 2 | v1.1 hỗ trợ `day` | Bỏ `day` khỏi danh sách; giữ `river` → 2; thêm `--days 0`/`6` → 2 |
| `test_smoke_p1.py:65-67` nút `attack` → mã 2 | v1.1: "nút đúng kiểu nhưng sai pha hoặc mở rộng chưa bật thì bỏ qua" (đề bản mới `:306`) → `attack: true` phải **mã 0** (bị bỏ qua) | Đổi test: `attack` → mã 0; giữ `jump` → mã 2 (P2-Q6) |
| `test_python_starter_units.py:46-50` `attack` không phải nút v1.0 | như trên | như trên |
| `test_inv_bad_schema_exit_2` `ca_la_lung` | vẫn đúng | giữ; thêm ca `ca_keo` hợp lệ |
| Test bơi/mép (`test_move_*`) | cá bơi không ảnh hưởng người chơi | giữ |

### 4.2 Nhóm test ẩn dễ gặp (theo AC của đề)
- **Số chuẩn**: ngạt ở đúng tick (chạm 0 tính bước 1), mất cả giỏ khi ngất, hết giờ giữ giỏ, cả đàn hay không, cooldown 30 tick từ lần bắt thành công, regrow 1.200, bến trước hái.
- **Cá**: đầu ca 8 đàn ở 8 điểm khác nhau thuộc tập điểm sinh; luôn ≤ 12; `fish_spawned` chỉ ở `phase_tick % 360 == 0`; cá nằm trong miền loài. Với `random_fish:false` + `fish[]`: cá **đứng yên**, không sinh → test so chính xác được.
- **Cá Sấu**: fixture `monsters[]` + `player` gần → `monster_hit{lost}` đúng LIFO và `floor(n/2)`; bất tử 90 tick không hit lại; recoil 60 bước; ngạt vẫn trừ Máu khi đang bất tử.
- **Quán**: 4 bàn ngồi theo id nhỏ nhất; khách tại 120 + 900·k; boa `floor`; đóng ca không trừ uy tín.
- **Day**: chuỗi `day_start → day_plan → phase_start(gather)` ở tick đầu; `phase_start(quan)` cùng tick với `gather_end`; `days_completed`; mua cấp xong chỉ có hiệu lực Ngày sau (`oxygen_max_ticks = 2700` ở Ngày 2); `buy_failed(funds)`, `max_level`; Shop tự đóng sau 600 tick; trần 22.200 tick/Ngày.
- **Pause**: `tick` tăng còn `sim_tick`/`phase_tick` đứng yên; `resumed` chạy gameplay ngay bước đó.
- **Mã 2**: `--days` ngoài 1–5 hoặc dùng với mode khác; `money > earned`; `quan.stock` khi chạy day; `ingredients` khai sai.

### 4.3 Tự kiểm tất định
- Mọi RNG mới đặt **tên luồng riêng** trong `Streams`: vd. `fish_init`, `fish_turn`, `fish_spawn`, `customer_dish`. Như vậy thêm Cá Sấu hay mở rộng không làm lệch chuỗi cá/khách.
- RNG cho từng đàn: nên rút theo thứ tự id cố định mỗi bước, hoặc dùng luồng `f"fish_turn:{id}"` để thêm/bớt đàn không làm lệch đàn khác.
- Test byte: chạy `--mode day --days 2 --seed 7` hai lần rồi `cmp`; thêm `PYTHONHASHSEED=random` để bắt lỗi duyệt `set`.
- Golden P1: lưu JSONL của vài fixture P1 với `random_fish:false` (cá đứng yên → output không phụ thuộc thuật toán RNG) và so byte ở mọi phase sau.
- Test ẩn **không thể** so vị trí cá ngẫu nhiên với một bản chuẩn (thuật toán RNG mỗi nhóm khác nhau), nên nhiều khả năng chỉ kiểm tính chất. Vị trí chính xác chỉ kiểm được qua fixture tắt ngẫu nhiên.

### 4.4 Ngân sách hiệu năng
- Một Ngày ≤ 22.200 tick ≤ 20 s → còn ~0,9 ms/tick. Hiện gather 22.200 tick chạy 0,09 s.
- Rủi ro: `sort_by_id` gọi nhiều lần mỗi tick (dùng regex), kiểm khoảng cách sinh cá O(36 × 12), snapshot quán có dict lớn. Vẫn thừa sức, nhưng nên có một test đo thời gian: `--mode day --days 5 --snapshot-every 1` < 20 s × 5.

---

## 5. Snapshot cần thêm cho UI (cho worker Cursor)

| Trường | Ở đâu | Dùng cho HUD |
|---|---|---|
| `state` | mọi snapshot | v1.0 `playing`/`finished` + `"paused"` (bản mới `:380`) → menu pause làm mờ nền |
| `phase` | đã có (`runner.py:31`) | `gather` / `quan` / `shop` → chọn cảnh |
| `phase_tick`, `sim_tick` | đã có, cần tách khỏi `tick` | |
| `day`, `day_plan` (Ngày hiện tại hoặc cả mảng), `upgrades`, `active_upgrades` | mọi pha khi mode `day` (§4.4 `:526-528`) | DayIntro (danh sách Má Tư), HUD "đã lấy/cần", Shop |
| `player.invuln_ticks` | gather (đã có) | nhấp nháy khi bất tử (UI đã đọc) |
| `monsters[]` | gather: `{id, kind, pos, state, target_idx, state_ticks_left, recoil_dir}` (GIẢ ĐỊNH theo schema scenario §4.3) | viền tím + "Thủy quái!" khi có con gần |
| `fish[]` thêm `age_ticks` | gather | không cần cho HUD |
| `stock` (dư) + `time_left_ticks` | Shop (§4.4 `:530-533`) | màn Shop |
| `money`, `earned`, `reputation`, `score` | đã có | |
| Tiền ca, khách phục vụ/bỏ đi, boa, thay đổi uy tín | **không có trong đề** | DayResult cần → nhóm tự thêm trường hoặc UI tự cộng từ event `paid`/`customer_left` |
| Món bán chạy | không có | Summary → UI đếm từ event `served`/`paid` |
| `menu`, `shop.upgrades` (giá, cấp) | **không có** trong snapshot; `live.py` `meta` chỉ là `tuning[mode]` | Đề xuất `live.py` gửi thêm `meta.menu`, `meta.shop`, `meta.day_plan`, và `meta` theo pha khi chạy day |

Các màn chỉ có ở UI (Menu chính, DayIntro 4 s, EveningIntro, DayResult, Summary, Settings) không có trong headless. `live.py` cần cách cho UI biết đang ở màn nào; GIẢ ĐỊNH: UI tự hiển thị theo `phase` + sự kiện `day_start`/`phase_start`/`shop_end`.

Phím mới: Esc/P → `pause`; Shop: phím chọn nâng cấp → `{"buy":"oxygen"}` / `{"buy":"hp"}` (bản mới `:296-297`), Enter → `shop_done`.

---

## 6. Rủi ro chính
1. **P1 chưa xong** (lát 2–4 TODO, chưa có tag `phase-1`). Test ẩn P2 kiểm lại P1 → làm P1 trước.
2. **File khung bắt buộc sửa** (mục 3). Nếu giữ luật "không sửa khung" thì không đạt v1.1. Cần quyết ngay ai sửa.
3. **Đề còn thiếu** sau khi chép lại (mục 7): điều kiện vị trí người chơi khi bị Cá Sấu hit, dạng `extensions`, cá bị bắt có biến mất không, `faint.data` khi ngất do ngạt.
4. `hold_full` data không thống nhất: code gửi `{"kind"}` (`gather.py:138`, `docs/contracts/README.md`), còn `specs/001-phase-1-core/contracts/events.md` ghi `{source_id}`. Chốt một bên.
5. Bắt cả đàn bằng `try_add_hold` từng món sẽ thêm thiếu (vd. còn 1 ô mà bắt cá linh).
6. Tách `tick`/`sim_tick`/`phase_tick` đụng `runner.py`, dễ vỡ test cũ (`test_session_steps_gather_and_dock` kiểm `snapshot()["tick"]`).

## 7. Câu hỏi mở — trạng thái sau khi đọc đề bản đầy đủ

| # | Câu hỏi | Trạng thái | Căn cứ (dòng trong `docs/prd/phase-2-ticket-02.md` bản mới) |
|---|---|---|---|
| P2-Q1 | `ca_keo_nuong.cook_s`? | **ĐÃ CÓ TRONG ĐỀ**: 6 s, giá 70 | `:133-137`. Đã điền vào JSON mục 1.4 |
| P2-Q2 | Giá trị `state` trong snapshot | **ĐÃ CÓ TRONG ĐỀ** (phần thêm): `state:"paused"`; `playing`/`finished` giữ như v1.0. Pha Shop dùng `phase:"shop"`, không phải `state` | `:380`, `:394-397` |
| P2-Q3 | `faint.data` | **ĐÃ CÓ một phần**: do bị chạm thì `{"cause":"monster","lost":[giỏ còn lại],"hp":0}`. **VẪN MỞ**: ngất do ngạt có thêm `lost`/`hp` không (GIẢ ĐỊNH giữ `{}` như v1.0) | `:416` |
| P2-Q4 | Chuỗi `buy` của nâng cấp lõi | **ĐÃ CÓ TRONG ĐỀ**: `"oxygen"`, `"hp"`; mở rộng: `"weapon"`, `"net"`, `"buy:<kind>"`/`"sell:<kind>"`; lệnh không hỗ trợ → `buy_failed` | `:294-306` |
| P2-Q5 | Trường thêm vào vỏ event day; `end.reason` | **ĐÃ CÓ TRONG ĐỀ**: trường `day` (ví dụ `day_plan` ở tick 0); `end` thêm `days_completed`, đủ Ngày thì `reason:"days_complete"` | `:436`, `:440-442` |
| P2-Q6 | `attack` khi không làm Lao | **ĐÃ CÓ TRONG ĐỀ**: "Nút đúng kiểu nhưng sai pha hoặc mở rộng chưa bật thì **bỏ qua**" → mã 0, không phải mã 2. Hệ quả: test `test_smoke_p1.py:65-67` và `test_python_starter_units.py:46-50` (đòi `attack` → mã 2) phải sửa, ghi lý do. `jump` vẫn là nút lạ → mã 2 | `:289-291`, `:306` |
| P2-Q7 | Hit Cá Sấu cần người chơi ở đâu | **VẪN MỞ**: bản mới vẫn trống chỗ "người chơi ở … và hết bất tử" (GIẢ ĐỊNH: dưới nước; trên thực tế Cá Sấu bị kẹp `d ≥ 10`, bán kính 1.5 nên người chơi luôn ở `d ≥ 8.5`, kết quả gần như không đổi) | `:70-71` |
| P2-Q8 | `extensions` là mảng hay object | **VẪN MỞ**: đề chỉ nói "khai mã ở `extensions` tại gốc manifest" (GIẢ ĐỊNH mảng chuỗi, vd. `["burn"]`) | `:223` |
| P2-Q9 | Đàn cá bị bắt có biến mất không | **VẪN MỞ**: đề không nói thẳng (GIẢ ĐỊNH biến mất, vì có trần 12 đàn và luật sinh thêm; clarify #14) | — |

Ghi thêm từ bản đầy đủ: `day_start`/`phase_start` có data `{}` (`:417-418`); `phase` ∈ `gather`/`quan`/`shop` (`:394-397`); ví dụ scenario day có tiền: `{"day":{"money":200,"earned":200},"gather":{"hold":["ca_loc","bong_sung","bong_sung"],"random_fish":false}}` (`:377`). Dữ liệu `paused`/`resumed` vẫn không có ô riêng (`:421`) → GIẢ ĐỊNH `{}`.
