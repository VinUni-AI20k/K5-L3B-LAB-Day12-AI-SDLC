# Credits

Liệt kê asset ngoài (nguồn, giấy phép) và công cụ hỗ trợ đã dùng trong dự án **Quán Ăn Chợ Nổi**.

## 3D Environment & Gameplay Assets (`godot/assets/external/`)

### 1. Cây miền Tây (`godot/assets/external/tropical/`) — CC0 1.0 Universal
- Nguồn: [Tropical Island and Palm Trees — 3DAssets.dev](https://3dassets.dev/packs/tropical-island-ecology)
- Giấy phép: **CC0 1.0 Universal**
- Danh sách file (đã dequantize về glTF 2.0 chuẩn cho Godot 4.5.1):
  - `coconut_tall.glb`, `coconut_lean.glb`, `nipa_palm.glb`, `mangrove_small.glb`, `mangrove_large.glb`, `mangrove_red.glb`, `banana_clump.glb`, `taro.glb`

### 2. Xuồng gỗ (`godot/assets/external/boats/`) — CC0 1.0 Universal
- Nguồn: [Flat Bottom Boat — tevy.dev](https://tevy.dev/models/flat-bottom-boat)
- Giấy phép: **CC0 1.0 Universal**
- Danh sách file (đã giải nén `EXT_meshopt_compression` & `KHR_mesh_quantization` cho Godot 4.5.1):
  - `flat_boat.glb`

### 3. Cá, Hoa Súng, Sen & Thủy sinh (`godot/assets/external/aquatic/`) — CC0 1.0 Universal
- Nguồn: [3DAssets.dev](https://3dassets.dev/) (Quiet Lake Fishing, Swamp and Mangrove, Fresh Produce)
- Giấy phép: **CC0 1.0 Universal**
- Danh sách file (đã dequantize cho Godot 4.5.1):
  - `fish_carp.glb`, `fish_perch.glb`, `fish_whole_raw.glb`, `lotus_clump.glb`, `lily_pads_blossom.glb`, `lily_pads_swamp.glb`

### 4. Nhân vật 3D (`godot/assets/external/characters/`) — CC0 1.0 Universal
- Nguồn: [3DAssets.dev](https://3dassets.dev/) (Low Poly Character Figures, Tidal Navigator)
- Giấy phép: **CC0 1.0 Universal**
- Danh sách file (đã dequantize cho Godot 4.5.1):
  - `villager_woman.glb` (base nhân vật Út Sen, ghép cùng `conical_hats.glb`), `villager_man.glb`, `tidal_navigator.glb`

### 5. Đèn lồng (`godot/assets/external/props/`) — CC0 1.0 Universal
- Nguồn: [3DAssets.dev](https://3dassets.dev/) (Imperial China Palace and Garden, Izakaya Alley)
- Giấy phép: **CC0 1.0 Universal**
- Danh sách file (đã dequantize cho Godot 4.5.1):
  - `lantern_silk.glb`, `lantern_paper.glb`

### 6. Bếp, Nồi, Bàn Ghế & Món Ăn (`godot/assets/external/kitchen/`) — CC0 1.0 Universal
- Nguồn: [KayKit Restaurant Bits 1.0 — Kay Lousberg](https://github.com/KayKit-Game-Assets/KayKit-Restaurant-Bits-1.0)
- Giấy phép: **CC0 1.0 Universal**
- Danh sách file (`.gltf` + `.bin` + `restaurantbits_texture.png`):
  - `stove_single`, `pot_A_stew`, `pan_A`, `stew_bowl`, `food_dinner`, `plate`, `bowl`, `table_round_A`, `chair_stool`, `cuttingboard`

### 7. Bối cảnh Chợ Nổi / River Delta (`godot/assets/external/river_delta/`) — 1DesignTool Game Use
- Nguồn: [River Delta Collection — 1DesignTool](https://1designtool.com/3d/collections/river-delta)
- Giấy phép: [1DesignTool 3D License](https://1designtool.com/3d/license) (cho phép dùng, sửa, tích hợp trong game; không phân phối lại như thư viện asset thô)
- Danh sách file:
  - `sampans.glb`, `long_tail_boat.glb`, `stilt_houses.glb`, `floating_docks.glb`, `rice_store.glb`, `nets.glb`, `fruit_baskets.glb`, `fish_traps.glb`, `monkey_bridge.glb`, `conical_hats.glb`

### 8. Shader & Showcase Scene
- `godot/shaders/mekong_water.gdshader`: Shader nước phù sa tự viết.
- `godot/scripts/delta_showcase.gd`, `godot/scenes/GatherRiver.tscn`, `godot/scenes/RestaurantNight.tscn`: Scene trưng bày bối cảnh & asset 3D Tây Nam Bộ (tương thích Godot 4.5.1).
