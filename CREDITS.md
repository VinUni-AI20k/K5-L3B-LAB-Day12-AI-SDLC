# Credits

Liệt kê asset ngoài (nguồn, giấy phép) và công cụ hỗ trợ đã dùng trong dự án **Quán Ăn Chợ Nổi**.

## 3D Environment Assets (`godot/assets/external/`)

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

### 3. Bối cảnh Chợ Nổi / River Delta (`godot/assets/external/river_delta/`) — 1DesignTool Game Use
- Nguồn: [River Delta Collection — 1DesignTool](https://1designtool.com/3d/collections/river-delta)
- Giấy phép: [1DesignTool 3D License](https://1designtool.com/3d/license) (cho phép dùng, sửa, tích hợp trong game; không phân phối lại như thư viện asset thô)
- Danh sách file:
  - `sampans.glb`, `long_tail_boat.glb`, `stilt_houses.glb`, `floating_docks.glb`, `rice_store.glb`, `nets.glb`, `fruit_baskets.glb`, `fish_traps.glb`, `monkey_bridge.glb`, `conical_hats.glb`

### 4. Shader & Showcase Scene
- `godot/shaders/mekong_water.gdshader`: Shader nước phù sa tự viết.
- `godot/scripts/delta_showcase.gd`, `godot/scenes/GatherRiver.tscn`, `godot/scenes/RestaurantNight.tscn`: Scene trưng bày bối cảnh 3D Tây Nam Bộ (tương thích Godot 4.5.1).
