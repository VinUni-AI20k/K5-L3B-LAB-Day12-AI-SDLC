extends Node3D

## Quán Ăn Chợ Nổi — Godot 4.5 3D Client & Preview
## - Kết nối trực tiếp tới `python3 -m chonoi.live --mode gather|quan --port 8000` qua HTTP (/state, /input, /restart).
## - Nếu chưa bật server `chonoi.live`, tự động chạy ở chế độ 3D Offline Sandbox (hỗ trợ cả cảnh Sông 3D và Quán Nổi 3D, phím Tab để chuyển cảnh) để kiểm thử đồ họa 3D và vượt qua `godot --headless --path godot --quit-after 5`.
## - Tuyệt đối không ảnh hưởng tới `python3 -m chonoi.headless` dùng để chấm điểm tự động.

const SERVER_URL := "http://127.0.0.1:8000"
const POLL_INTERVAL := 0.033

var mode: String = "gather"
var connected: bool = false
var poll_timer: float = 0.0
var poll_busy: bool = false
var last_sent_input: String = ""

# Trạng thái hiển thị (cập nhật từ server snapshot hoặc offline sandbox)
var player_pos: Vector2 = Vector2(2.0, 0.0)
var player_heading_deg: float = 0.0
var oxygen_ratio: float = 1.0
var hp: int = 3
var hp_max: int = 3
var hold_items: Array = []
var hold_cap: int = 12
var money: int = 0
var reputation: float = 3.0
var score: int = 300
var time_left_s: int = 180

var nodes_data: Array = [
	{"id": "N1", "kind": "bong_dien_dien", "pos": [12.0, 0.0], "ready": true},
	{"id": "N2", "kind": "bong_dien_dien", "pos": [28.0, 0.0], "ready": true},
	{"id": "N3", "kind": "bong_sung", "pos": [44.0, 0.0], "ready": true},
	{"id": "N4", "kind": "bong_sung", "pos": [60.0, 0.0], "ready": true},
]
var fish_data: Array = [
	{"id": "F1", "kind": "ca_linh", "pos": [15.0, 5.0], "heading_deg": 0.0},
	{"id": "F2", "kind": "ca_loc", "pos": [30.0, 10.0], "heading_deg": 0.0},
	{"id": "F3", "kind": "ca_linh", "pos": [45.0, 10.0], "heading_deg": 0.0},
	{"id": "F4", "kind": "ca_loc", "pos": [60.0, 16.0], "heading_deg": 0.0},
	{"id": "F5", "kind": "ca_linh", "pos": [75.0, 5.0], "heading_deg": 0.0},
	{"id": "F6", "kind": "ca_loc", "pos": [90.0, 16.0], "heading_deg": 0.0},
]
var stoves_data: Array = [
	{"id": "B1", "pos": [2.0, 8.0], "state": "idle", "dish": null},
]
var tables_data: Array = [
	{"id": "T1", "pos": [9.0, 2.0], "customer_id": null},
]
var customers_data: Array = []

# Nodes 3D
var camera: Camera3D
var dir_light: DirectionalLight3D
var gather_root: Node3D
var quan_root: Node3D
var player_mesh_gather: Node3D
var player_mesh_quan: Node3D
var dynamic_gather_container: Node3D
var dynamic_quan_container: Node3D

# Nodes UI
var hud_label: Label
var status_label: Label
var http_poll: HTTPRequest
var http_input: HTTPRequest


func _ready() -> void:
	_setup_environment_3d()
	_build_gather_3d_world()
	_build_quan_3d_world()
	_setup_hud()
	_setup_http_clients()
	_rebuild_dynamic_entities()
	_update_mode_visibility()


func _setup_environment_3d() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.07, 0.14, 0.22)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.65, 0.78, 0.88)
	env.ambient_light_energy = 0.85
	var world_env := WorldEnvironment.new()
	world_env.environment = env
	add_child(world_env)

	dir_light = DirectionalLight3D.new()
	dir_light.rotation_degrees = Vector3(-50.0, -30.0, 0.0)
	dir_light.light_energy = 1.25
	dir_light.shadow_enabled = true
	add_child(dir_light)

	camera = Camera3D.new()
	camera.position = Vector3(12.0, 3.0, 22.0)
	camera.fov = 55.0
	add_child(camera)


func _make_box(size: Vector3, col: Color, pos: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	var mat := StandardMaterial3D.new()
	mat.albedo_color = col
	bm.material = mat
	mi.mesh = bm
	mi.position = pos
	return mi


func _make_sphere(radius: float, col: Color, pos: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = radius
	sm.height = radius * 2.0
	var mat := StandardMaterial3D.new()
	mat.albedo_color = col
	sm.material = mat
	mi.mesh = sm
	mi.position = pos
	return mi


func _build_gather_3d_world() -> void:
	gather_root = Node3D.new()
	gather_root.name = "GatherWorld3D"
	add_child(gather_root)

	# Mặt nước sông 3D (x từ 0..100, y = 0)
	var water_surface := _make_box(Vector3(104.0, 0.25, 8.0), Color(0.28, 0.72, 0.92), Vector3(50.0, 0.0, 0.0))
	gather_root.add_child(water_surface)

	# Lòng sông sâu 3D (d từ 0..30 -> y từ 0..-30)
	var river_backdrop := _make_box(Vector3(104.0, 30.0, 1.0), Color(0.05, 0.18, 0.30), Vector3(50.0, -15.0, -3.5))
	gather_root.add_child(river_backdrop)

	# Đáy sông tại d = 30 (y = -30)
	var river_bed := _make_box(Vector3(104.0, 1.0, 8.0), Color(0.24, 0.19, 0.14), Vector3(50.0, -30.5, 0.0))
	gather_root.add_child(river_bed)

	# Bến thuyền nổi tại dock_pos = [2, 0]
	var dock := _make_box(Vector3(4.0, 0.8, 4.5), Color(0.55, 0.38, 0.22), Vector3(2.0, 0.5, 0.0))
	var dock_roof := _make_box(Vector3(4.4, 0.4, 4.8), Color(0.75, 0.28, 0.20), Vector3(2.0, 2.3, 0.0))
	gather_root.add_child(dock)
	gather_root.add_child(dock_roof)

	# Nhân vật Út Sen 3D (Gather)
	player_mesh_gather = Node3D.new()
	var body := _make_sphere(0.75, Color(1.0, 0.54, 0.24), Vector3.ZERO)
	var visor := _make_box(Vector3(0.7, 0.35, 0.5), Color(0.95, 0.98, 1.0), Vector3(0.55, 0.15, 0.0))
	player_mesh_gather.add_child(body)
	player_mesh_gather.add_child(visor)
	gather_root.add_child(player_mesh_gather)

	dynamic_gather_container = Node3D.new()
	gather_root.add_child(dynamic_gather_container)


func _build_quan_3d_world() -> void:
	quan_root = Node3D.new()
	quan_root.name = "QuanWorld3D"
	add_child(quan_root)

	# Sàn ghe / quán ăn nổi 3D (x: 0..16, z: 0..10 -> Godot X: 0..16, Z: 0..-10)
	var deck := _make_box(Vector3(16.0, 0.5, 10.0), Color(0.78, 0.62, 0.40), Vector3(8.0, -0.25, -5.0))
	var water_around := _make_box(Vector3(28.0, 0.2, 22.0), Color(0.12, 0.38, 0.55), Vector3(8.0, -0.6, -5.0))
	quan_root.add_child(water_around)
	quan_root.add_child(deck)

	# Nhân vật Út Sen 3D (Quán)
	player_mesh_quan = Node3D.new()
	var body := _make_box(Vector3(0.8, 1.4, 0.8), Color(1.0, 0.54, 0.24), Vector3(0.0, 0.7, 0.0))
	var hat := _make_sphere(0.5, Color(0.95, 0.82, 0.35), Vector3(0.0, 1.55, 0.0))
	player_mesh_quan.add_child(body)
	player_mesh_quan.add_child(hat)
	quan_root.add_child(player_mesh_quan)

	dynamic_quan_container = Node3D.new()
	quan_root.add_child(dynamic_quan_container)


func _setup_hud() -> void:
	var canvas := CanvasLayer.new()
	add_child(canvas)

	var panel := ColorRect.new()
	panel.color = Color(0.04, 0.08, 0.12, 0.78)
	panel.position = Vector2(12, 12)
	panel.size = Vector2(936, 92)
	canvas.add_child(panel)

	hud_label = Label.new()
	hud_label.position = Vector2(24, 18)
	hud_label.add_theme_font_size_override("font_size", 18)
	hud_label.text = "Quán Ăn Chợ Nổi 3D — Đang khởi tạo..."
	canvas.add_child(hud_label)

	status_label = Label.new()
	status_label.position = Vector2(24, 52)
	status_label.add_theme_font_size_override("font_size", 14)
	status_label.text = "WASD/Mũi tên: Di chuyển | E: Tương tác (Hái/Cập bến/Bếp/Bàn) | Space: Bắt cá | R: Chơi lại | Tab: Đổi cảnh Gather/Quán (Offline)"
	canvas.add_child(status_label)


func _setup_http_clients() -> void:
	http_poll = HTTPRequest.new()
	add_child(http_poll)
	http_poll.request_completed.connect(_on_poll_completed)

	http_input = HTTPRequest.new()
	add_child(http_input)


func _rebuild_dynamic_entities() -> void:
	for c in dynamic_gather_container.get_children():
		c.queue_free()
	for n in nodes_data:
		var ready: bool = n.get("ready", true)
		var kind: String = str(n.get("kind", "bong_dien_dien"))
		var col := Color(0.95, 0.76, 0.18) if kind == "bong_dien_dien" else Color(0.91, 0.47, 0.61)
		if not ready:
			col = col.darkened(0.55)
		var pos: Array = n.get("pos", [0.0, 0.0])
		var node_mesh := _make_sphere(0.65, col, Vector3(float(pos[0]), -float(pos[1]) + 0.35, 0.0))
		dynamic_gather_container.add_child(node_mesh)

	for f in fish_data:
		var kind: String = str(f.get("kind", "ca_linh"))
		var col := Color(0.84, 0.90, 0.95) if kind == "ca_linh" else Color(0.48, 0.65, 0.32)
		var pos: Array = f.get("pos", [15.0, 5.0])
		var fish_mesh := _make_box(Vector3(1.3, 0.55, 0.5), col, Vector3(float(pos[0]), -float(pos[1]), 0.0))
		dynamic_gather_container.add_child(fish_mesh)

	for c in dynamic_quan_container.get_children():
		c.queue_free()
	for st in stoves_data:
		var state: String = str(st.get("state", "idle"))
		var col := Color(0.91, 0.54, 0.17) if state == "cooking" else (Color(0.43, 0.75, 0.35) if state == "ready" else Color(0.42, 0.42, 0.45))
		var pos: Array = st.get("pos", [2.0, 8.0])
		var stove_mesh := _make_box(Vector3(1.5, 1.1, 1.5), col, Vector3(float(pos[0]), 0.55, -float(pos[1])))
		dynamic_quan_container.add_child(stove_mesh)

	for tb in tables_data:
		var pos: Array = tb.get("pos", [9.0, 2.0])
		var table_mesh := _make_box(Vector3(1.6, 0.85, 1.6), Color(0.54, 0.35, 0.18), Vector3(float(pos[0]), 0.42, -float(pos[1])))
		dynamic_quan_container.add_child(table_mesh)
		if tb.get("customer_id") != null:
			var cust_mesh := _make_sphere(0.55, Color(0.95, 0.71, 0.76), Vector3(float(pos[0]), 1.35, -float(pos[1]) - 1.1))
			dynamic_quan_container.add_child(cust_mesh)


func _update_mode_visibility() -> void:
	gather_root.visible = (mode == "gather")
	quan_root.visible = (mode == "quan")


func _physics_process(delta: float) -> void:
	var ix := Input.get_axis("ui_left", "ui_right")
	var iy := Input.get_axis("ui_up", "ui_down")
	var interact_pressed := Input.is_key_pressed(KEY_E)
	var catch_pressed := Input.is_key_pressed(KEY_SPACE)

	if Input.is_action_just_pressed("ui_focus_next") and not connected:
		mode = "quan" if mode == "gather" else "gather"
		player_pos = Vector2(2.0, 0.0) if mode == "gather" else Vector2(8.0, 5.0)
		_update_mode_visibility()

	# Gửi input lên server Python nếu đang kết nối
	if connected:
		var dy := iy if mode == "gather" else -iy
		var payload := JSON.stringify({"move": [ix, dy], "interact": interact_pressed, "catch": catch_pressed})
		if payload != last_sent_input:
			last_sent_input = payload
			http_input.cancel_request()
			http_input.request(SERVER_URL + "/input", ["Content-Type: application/json"], HTTPClient.METHOD_POST, payload)
	else:
		# Offline 3D Sandbox fallback khi chưa bật server chonoi.live
		var speed := 4.0
		if mode == "gather":
			player_pos.x = clampf(player_pos.x + ix * speed * delta, 0.0, 100.0)
			player_pos.y = clampf(player_pos.y + iy * speed * delta, 0.0, 30.0)
			if player_pos.y > 0.5:
				oxygen_ratio = maxf(0.0, oxygen_ratio - delta / 30.0)
			else:
				oxygen_ratio = minf(1.0, oxygen_ratio + delta * 0.2)
		else:
			player_pos.x = clampf(player_pos.x + ix * speed * delta, 0.0, 16.0)
			player_pos.y = clampf(player_pos.y - iy * speed * delta, 0.0, 10.0)

	# Cập nhật vị trí Mesh 3D và Camera3D góc nhìn thứ ba
	if mode == "gather":
		var target_3d := Vector3(player_pos.x, -player_pos.y, 0.0)
		player_mesh_gather.position = target_3d
		camera.position = camera.position.lerp(Vector3(clampf(player_pos.x, 10.0, 90.0), clampf(-player_pos.y + 2.0, -24.0, 4.0), 22.0), delta * 6.0)
		camera.look_at(Vector3(clampf(player_pos.x, 10.0, 90.0), clampf(-player_pos.y, -26.0, 0.0), 0.0), Vector3.UP)
	else:
		var target_3d := Vector3(player_pos.x, 0.0, -player_pos.y)
		player_mesh_quan.position = target_3d
		camera.position = camera.position.lerp(Vector3(8.0, 11.5, 4.5), delta * 6.0)
		camera.look_at(Vector3(8.0, 0.0, -5.0), Vector3.UP)

	# Định kỳ poll /state từ chonoi.live
	poll_timer += delta
	if poll_timer >= POLL_INTERVAL and not poll_busy:
		poll_timer = 0.0
		poll_busy = true
		http_poll.request(SERVER_URL + "/state")

	_refresh_hud_text()


func _on_poll_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	poll_busy = false
	if result != HTTPRequest.RESULT_SUCCESS or response_code != 200:
		connected = false
		return
	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY:
		return
	connected = true
	var new_mode: String = str(parsed.get("mode", mode))
	if new_mode != mode:
		mode = new_mode
		_update_mode_visibility()

	time_left_s = int(ceil(float(parsed.get("time_left_ticks", 0)) / 60.0))
	money = int(parsed.get("money", 0))
	reputation = float(parsed.get("reputation", 3.0))
	score = int(parsed.get("score", 0))

	var p = parsed.get("player", {})
	if typeof(p) == TYPE_DICTIONARY and p.has("pos"):
		var pos_arr: Array = p["pos"]
		player_pos = Vector2(float(pos_arr[0]), float(pos_arr[1]))
		var o_ticks := float(p.get("oxygen_ticks", 1800))
		var o_max := maxf(1.0, float(p.get("oxygen_max_ticks", 1800)))
		oxygen_ratio = o_ticks / o_max
		hp = int(p.get("hp", 3))
		hp_max = int(p.get("hp_max", 3))

	if mode == "gather":
		hold_items = parsed.get("hold", [])
		hold_cap = int(parsed.get("hold_capacity", 12))
		nodes_data = parsed.get("nodes", nodes_data)
		fish_data = parsed.get("fish", fish_data)
	else:
		stoves_data = parsed.get("stoves", stoves_data)
		tables_data = parsed.get("tables", tables_data)
		customers_data = parsed.get("customers", customers_data)
	_rebuild_dynamic_entities()


func _refresh_hud_text() -> void:
	var conn_tag := "[LIVE: Kết nối chonoi.live:8000]" if connected else "[OFFLINE 3D PREVIEW - Bật `python3 -m chonoi.live` để đồng bộ]"
	if mode == "gather":
		hud_label.text = "%s | Buổi Sáng (Gather 3D) | Giờ: %ds | Vị trí: (%.1f, d=%.1fm) | Oxy: %d%% | Máu: %d/%d | Giỏ: %d/%d" % [
			conn_tag, time_left_s, player_pos.x, player_pos.y, int(round(oxygen_ratio * 100.0)), hp, hp_max, hold_items.size(), hold_cap
		]
	else:
		hud_label.text = "%s | Buổi Tối (Quán Nổi 3D) | Giờ: %ds | Vị trí: (%.1f, z=%.1fm) | Tiền: %dk | Uy tín: %.1f | Điểm: %d" % [
			conn_tag, time_left_s, player_pos.x, player_pos.y, money, reputation, score
		]
