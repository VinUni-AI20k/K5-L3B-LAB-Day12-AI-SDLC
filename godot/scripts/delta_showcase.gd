extends Node3D
## Art-only 3D showcase: not the game's headless simulation.
## Assets are downloaded from their authors by tools/download_assets.py.
@export_enum("gather", "quan") var stage: String = "gather"

var cam: Camera3D
var focus: Vector3
var distance := 65.0
var azimuth := 0.65
var elevation := 0.56
var orbit := false
var loaded_models := 0
var missing_models := {}
var rng := RandomNumberGenerator.new()

const WATER_LEVEL := 0.30
const MUD := "#82694a"
const BANK := "#958054"
const WOOD := "#6a442c"
const WOOD_LIGHT := "#b58b5b"
const ROOF := "#8f7549"
const GOLD := "#efb55a"
const FOLIAGE := "#4a804a"
const LANTERN := "#ffd77b"

func _ready() -> void:
    rng.seed = 20261121
    _lighting_and_sky()
    _landscape()
    if stage == "gather":
        _gather_scene()
        focus = Vector3(0.0, 1.5, 0.0)
        distance = 72.0
        azimuth = 0.64
        elevation = 0.54
    else:
        _restaurant_scene()
        focus = Vector3(0.0, 2.5, 0.0)
        distance = 38.0
        azimuth = 0.78
        elevation = 0.60
    _camera()
    _overlay()
    print("Tay Nam Bo 3D / stage=", stage, "/ imported models placed=", loaded_models)
    if not missing_models.is_empty():
        print("Missing source GLBs; run python3 tools/download_assets.py --all: ", missing_models.keys())

func _material(c: String, metal := 0.0, rough := 0.87) -> StandardMaterial3D:
    var m := StandardMaterial3D.new()
    m.albedo_color = Color(c)
    m.roughness = rough
    m.metallic = metal
    return m

func _box(pos: Vector3, scale: Vector3, color: String, parent: Node3D = self) -> MeshInstance3D:
    var node := MeshInstance3D.new()
    var mesh := BoxMesh.new()
    mesh.size = scale
    node.mesh = mesh
    node.material_override = _material(color)
    node.position = pos
    parent.add_child(node)
    return node

func _cylinder(pos: Vector3, radius: float, height: float, color: String, parent: Node3D = self) -> MeshInstance3D:
    var node := MeshInstance3D.new()
    var mesh := CylinderMesh.new()
    mesh.top_radius = radius * 0.88
    mesh.bottom_radius = radius
    mesh.height = height
    mesh.radial_segments = 10
    node.mesh = mesh
    node.material_override = _material(color)
    node.position = pos
    parent.add_child(node)
    return node

func _asset(family: String, asset_id: String, at: Vector3, scale := 1.0, yaw := 0.0) -> Node3D:
    var path := "res://assets/external/%s/%s.glb" % [family, asset_id]
    if not ResourceLoader.exists(path):
        missing_models[asset_id] = true
        return null
    var packed = load(path)
    if not (packed is PackedScene):
        missing_models[asset_id] = true
        return null
    var instance: Node3D = packed.instantiate()
    instance.name = asset_id
    instance.position = at
    instance.rotation.y = yaw
    instance.scale = Vector3.ONE * scale
    add_child(instance)
    loaded_models += 1
    return instance

func _lighting_and_sky() -> void:
    var world := WorldEnvironment.new()
    var env := Environment.new()
    var sky := Sky.new()
    var sky_mat := ProceduralSkyMaterial.new()
    if stage == "gather":
        sky_mat.sky_top_color = Color("#7eacc1")
        sky_mat.sky_horizon_color = Color("#f3c99d")
        sky_mat.ground_bottom_color = Color("#4a6861")
        sky_mat.ground_horizon_color = Color("#ebc6a1")
    else:
        sky_mat.sky_top_color = Color("#1a3452")
        sky_mat.sky_horizon_color = Color("#9c6d7a")
        sky_mat.ground_bottom_color = Color("#253847")
        sky_mat.ground_horizon_color = Color("#735a67")
    sky.sky_material = sky_mat
    env.background_mode = Environment.BG_SKY
    env.sky = sky
    env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
    env.reflected_light_source = Environment.REFLECTION_SOURCE_BG
    env.ambient_light_energy = 0.84 if stage == "gather" else 0.50
    env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
    env.fog_enabled = true
    env.fog_light_color = Color("#c9ac92") if stage == "gather" else Color("#7d6b81")
    env.fog_density = 0.0045 if stage == "gather" else 0.0060
    world.environment = env
    add_child(world)
    var sun := DirectionalLight3D.new()
    sun.name = "SunsetSun"
    sun.rotation_degrees = Vector3(-48.0, -42.0, 0.0)
    sun.light_color = Color("#ffe0ab") if stage == "gather" else Color("#caa3a0")
    sun.light_energy = 1.35 if stage == "gather" else 0.68
    sun.shadow_enabled = true
    add_child(sun)
    if stage == "quan":
        for x in [-4.0, 0.0, 4.0]:
            var lamp := OmniLight3D.new()
            lamp.position = Vector3(x, 5.4, 0.4)
            lamp.light_color = Color(LANTERN)
            lamp.light_energy = 1.1
            lamp.omni_range = 9.0
            add_child(lamp)

func _landscape() -> void:
    _box(Vector3(0.0, -2.50, 0.0), Vector3(34.5, 0.50, 176.0), MUD)
    _river_banks()
    var water := MeshInstance3D.new()
    water.name = "MekongRiver_3D_DepthWater"
    var m := PlaneMesh.new()
    m.size = Vector2(34.0, 176.0)
    m.subdivide_width = 135
    m.subdivide_depth = 200
    water.mesh = m
    water.position.y = WATER_LEVEL
    var water_mat := ShaderMaterial.new()
    water_mat.shader = load("res://shaders/mekong_water.gdshader")
    water.material_override = water_mat
    add_child(water)
    _vegetation()
    # River particles (floating plant and ripples) kept at the edges.
    for j in range(35):
        var z := rng.randf_range(-76, 76)
        var x: float = (1.0 if j % 2 == 0 else -1.0) * rng.randf_range(11.6, 16.0)
        var duckweed := _cylinder(Vector3(x, WATER_LEVEL+0.035, z), rng.randf_range(.25,.58), .025, "#5f9456")
        duckweed.rotation.y = rng.randf_range(-3.14,3.14)

func _river_banks() -> void:
    # Actual sloping 3D riverbed banks rather than a side-view background image.
    for side in [-1.0, 1.0]:
        var surface := SurfaceTool.new()
        surface.begin(Mesh.PRIMITIVE_TRIANGLES)
        for i in range(128):
            var z0 := -88.0 + i * 1.38
            var z1 := z0 + 1.38
            for a in [0.0, 1.0]:
                var za: float = z0 if a == 0.0 else z1
                var curve: float = 0.75 * sin(za*0.047) + 0.5*cos(za*0.097)
                var inner := Vector3(side*(16.6+curve), -1.9, za)
                var shore := Vector3(side*(17.6+curve), 0.33, za)
                var high := Vector3(side*(22.0+curve), 1.25, za)
                var outer := Vector3(side*(42.0+curve), 1.60, za)
                if a == 0.0:
                    _bank_strip_a = [inner, shore, high, outer]
                else:
                    var next := [inner, shore, high, outer]
                    for n in range(3):
                        surface.set_color(Color(BANK) if n>0 else Color(MUD))
                        surface.add_vertex(_bank_strip_a[n]); surface.add_vertex(next[n]); surface.add_vertex(_bank_strip_a[n+1])
                        surface.add_vertex(_bank_strip_a[n+1]); surface.add_vertex(next[n]); surface.add_vertex(next[n+1])
        surface.generate_normals()
        var mesh_instance := MeshInstance3D.new()
        mesh_instance.mesh = surface.commit()
        mesh_instance.material_override = _material(BANK)
        mesh_instance.name = "Natural3DShoreLeft" if side<0 else "Natural3DShoreRight"
        add_child(mesh_instance)

var _bank_strip_a := []

func _vegetation() -> void:
    # Varying tree height, yaw and distance gives genuine near/mid/far depth.
    for i in range(120):
        var side := -1.0 if i % 2 == 0 else 1.0
        var z := rng.randf_range(-86.0, 86.0)
        var x := side * rng.randf_range(18.5, 38.0)
        var near_shore: bool = absf(x) < 23.0
        var y := 0.78 if near_shore else 1.59
        var type := rng.randi_range(0, 7)
        if near_shore and type <= 2:
            _asset("tropical", "nipa_palm", Vector3(x, y, z), rng.randf_range(.66,1.15), rng.randf_range(-3.14,3.14))
        elif type == 0:
            _asset("tropical", "banana_clump", Vector3(x,y,z), rng.randf_range(.85,1.35), rng.randf_range(-3.14,3.14))
        elif type <= 4:
            _asset("tropical", "coconut_tall", Vector3(x,y,z), rng.randf_range(.7,1.25), rng.randf_range(-3.14,3.14))
        elif type <= 5:
            _asset("tropical", "coconut_lean", Vector3(x,y,z), rng.randf_range(.72,1.10), rng.randf_range(-3.14,3.14))
        elif type == 6:
            _asset("tropical", "mangrove_small", Vector3(x,y,z), rng.randf_range(.75,1.1), rng.randf_range(-3.14,3.14))
        else:
            _asset("tropical", "taro", Vector3(x,y,z), rng.randf_range(.95,1.4), rng.randf_range(-3.14,3.14))
    for i in range(24):
        var side := -1.0 if i % 2 == 0 else 1.0
        var z := rng.randf_range(-83, 83)
        var x := side * rng.randf_range(16.9, 19.6)
        _asset("tropical", "mangrove_large", Vector3(x,0.20,z), rng.randf_range(.85,1.05))

func _gather_scene() -> void:
    for i in range(8):
        var z := -59.0 + i*17.0
        var side := -1.0 if i%2==0 else 1.0
        _asset("river_delta", "stilt_houses", Vector3(side*24.0,0.15,z),rng.randf_range(.85,1.25), (1.57 if side < 0 else -1.57))
        if i % 2 == 0:
            _asset("river_delta", "floating_docks", Vector3(side*13.6,0.1,z+4.0), 1.0)
    for i in range(12):
        var z := -63.0 + i*11.1
        var x := rng.randf_range(-10.0,10.0)
        var at := Vector3(x,0.21,z)
        if i % 3 == 0:
            _asset("river_delta", "sampans", at,.68,rng.randf_range(-.4,.4))
        elif i % 3 == 1:
            _asset("river_delta", "long_tail_boat", at,.62,rng.randf_range(-.8,.8))
        else:
            _asset("boats", "flat_boat", at,1.15,rng.randf_range(-.8,.8))
    _asset("river_delta", "rice_store", Vector3(-28,0.58,-2.5), 1.1,1.57)
    for i in range(6):
        _asset("river_delta", "fruit_baskets", Vector3(-13.3,0.6,-54.0+i*19.0),0.7)
        _asset("river_delta", "nets", Vector3(13.5,0.6,-56.0+i*19.0),0.85)

func _restaurant_scene() -> void:
    # Restaurant raft is an actual elevated timber floor with a readable 16 x 10m play area.
    _box(Vector3(0.0,0.93,0.0),Vector3(16.4,.38,10.4),WOOD)
    for i in range(40):
        _box(Vector3(-7.95+i*.40,1.15,0),Vector3(.28,.055,10.1), WOOD_LIGHT if i%4 else "#93704e")
    for x in [-7.1,-4.0,0.0,4.0,7.1]:
        for z in [-4.6,4.6]:
            _cylinder(Vector3(x,-0.25,z),.18,2.35,WOOD)
    # Big pitched thatched roof over cooking zone, supported by real 3D beams.
    for x in [-7.0,-2.0]:
        for z in [1.7,4.5]:
            _cylinder(Vector3(x,2.8,z),.12,4.4,WOOD)
    var roof_a = _box(Vector3(-4.5,5.10,2.40),Vector3(6.8,.20,3.7),ROOF)
    roof_a.rotation.z = 0.12
    for i in range(22):
        var x := -7.8+i*.30
        _box(Vector3(x,5.22,2.45),Vector3(.055,.055,3.62),"#cab374")
    # Kitchen B1 and table T1: keep the PRD semantic positions labelled.
    _box(Vector3(-4.9,1.60,2.9),Vector3(2.3,.76,1.4),"#62442e")
    _cylinder(Vector3(-4.9,2.12,2.9),.48,.24,"#3a3634")
    _box(Vector3(2.0,1.62,-1.6),Vector3(2.4,.17,1.65),WOOD_LIGHT)
    for x in [1.05,2.95]:
        for z in [-2.25,-.95]:
            _cylinder(Vector3(x,1.18,z),.10,.58,WOOD)
    for p in [Vector2(-4.9, 3.8), Vector2(2.0, -1.6)]:
        _cylinder(Vector3(p.x, 1.96, p.y), .28, .10, "#f3eee0")
    # Wooden lantern beam with warm lantern blocks.
    _box(Vector3(0.0,5.5,-3.85),Vector3(15.3,.10,.10),WOOD)
    for i in range(11):
        var x := -7.0+i*1.4
        _box(Vector3(x,4.95,-3.85),Vector3(.22,.54,.22),LANTERN)
        _box(Vector3(x,5.23,-3.85),Vector3(.32,.08,.32),WOOD)
    # Grape / fruit trading and bamboo market identity from actual Delta assets.
    for i in range(5):
        var z := -40.0 + i*20.0
        var side := -1.0 if i%2==0 else 1.0
        _asset("river_delta", "stilt_houses",Vector3(side*25.0,0.40,z),1.1,1.57 if side<0 else -1.57)
        _asset("river_delta", "floating_docks",Vector3(side*14.0,.12,z+3.0),1.0)
        _asset("river_delta", "sampans",Vector3(side*5.0,.16,z+6.0),.75,rng.randf_range(-1,1))
    for i in range(3):
        _asset("river_delta", "long_tail_boat",Vector3(-10.0+i*9.5,.18,-10.0-i*6),.67,rng.randf_range(-.3,.7))
    _asset("river_delta", "rice_store",Vector3(-26,.75,2.0),.92,1.57)
    for p in [Vector2(6.0, -4.0), Vector2(-6.0, -4.0), Vector2(0.0, 4.0)]:
        _asset("river_delta", "fruit_baskets", Vector3(p.x, 1.28, p.y), .7)
        _asset("river_delta", "fish_traps", Vector3(p.x, 1.28, p.y + 1.0), .4)
    _asset("river_delta", "delta_boat_seller",Vector3(12,.45,-12),.75)

func _camera() -> void:
    cam = Camera3D.new()
    cam.name = "REAL_PERSPECTIVE_CAMERA"
    cam.projection = Camera3D.PROJECTION_PERSPECTIVE
    cam.fov = 50.0
    cam.near = 0.07
    cam.far = 450.0
    cam.current = true
    add_child(cam)
    _camera_update()

func _camera_update() -> void:
    if not is_instance_valid(cam): return
    cam.position = focus + Vector3(distance*cos(elevation)*sin(azimuth), distance*sin(elevation), distance*cos(elevation)*cos(azimuth))
    cam.look_at(focus)

func _overlay() -> void:
    var canvas := CanvasLayer.new()
    add_child(canvas)
    var hint := Label.new()
    hint.text = "CHO NOI TAY NAM BO | F1: SONG | F2: QUAN BE | F3: LONG SONG | CHUOT PHAI: XOAY | CUON: ZOOM"
    hint.position = Vector2(18, 15)
    hint.add_theme_color_override("font_color", Color("#fff1cb"))
    hint.add_theme_font_size_override("font_size", 16)
    canvas.add_child(hint)
    if loaded_models == 0:
        var missing := Label.new()
        missing.text = "Chua cai asset: chay 'python3 tools/download_assets.py --all' roi mo lai project"
        missing.position = Vector2(18,48)
        missing.add_theme_color_override("font_color", Color("#ffcb9d"))
        canvas.add_child(missing)

func _unhandled_input(ev: InputEvent) -> void:
    if ev is InputEventKey and ev.pressed and not ev.echo:
        if ev.keycode == KEY_F1: get_tree().change_scene_to_file("res://scenes/GatherRiver.tscn")
        if ev.keycode == KEY_F2: get_tree().change_scene_to_file("res://scenes/RestaurantNight.tscn")
        if ev.keycode == KEY_F3: get_tree().change_scene_to_file("res://scenes/UnderwaterRiver.tscn")
    elif ev is InputEventMouseButton:
        if ev.button_index == MOUSE_BUTTON_RIGHT: orbit = ev.pressed
        elif ev.pressed and ev.button_index == MOUSE_BUTTON_WHEEL_UP:
            distance = max(7.0, distance*.88)
            _camera_update()
        elif ev.pressed and ev.button_index == MOUSE_BUTTON_WHEEL_DOWN:
            distance = min(180.0,distance*1.12)
            _camera_update()
    elif ev is InputEventMouseMotion and orbit:
        azimuth -= ev.relative.x*.006
        elevation = clamp(elevation + ev.relative.y*.004, .12, 1.38)
        _camera_update()
