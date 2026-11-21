# UI cảnh báo Phase 4 (T413, TV6)

Chỉ lớp hiển thị trong `chonoi/web/index.html`. Không đổi luật sim.

| Cảnh báo | Cách hiện | Thử |
|---|---|---|
| Thủy quái gần | Banner "⚠ Thủy quái gần!" + viền | `?demo=warn` (quái cạnh người chơi) |
| Oxy sắp hết | Banner khi oxy &lt; 25%; "Hết hơi!" khi oxy = 0 | cùng `?demo=warn` (200/1800 tick) |
| Khách sắp giận | Banner + chữ "sắp giận" khi kiên nhẫn &lt; 25% | `?demo=warnq` |
| Tương phản cao | Viền vàng, chữ vàng trên nền đen, phím **C** hoặc nút menu | `?contrast=1` hoặc hai URL demo trên (bật sẵn) |

Chữ HUD vẫn ≥ 18 px.
