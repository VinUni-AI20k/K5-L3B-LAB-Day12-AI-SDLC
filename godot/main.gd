extends Node2D

# Pixel-based movement for checking input in the starter scene.
const PREVIEW_SPEED := 240.0
const MARKER_MARGIN := Vector2(12.0, 12.0)

@onready var marker: Polygon2D = $Marker


func _physics_process(delta: float) -> void:
	var direction := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	var next_position := marker.position + direction * PREVIEW_SPEED * delta
	var viewport_size := get_viewport_rect().size
	marker.position = next_position.clamp(MARKER_MARGIN, viewport_size - MARKER_MARGIN)
