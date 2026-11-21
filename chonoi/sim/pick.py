"""Chọn đối tượng gần nhất trong bán kính (dùng chung cho buổi sáng và buổi tối).

Chủ: Phạm Quốc Huy (Integrator).
Không fallback: chỉ trả đúng MỘT cặp (rank, obj) nhỏ nhất theo (khoảng cách, rank, id_key(id)),
hoặc None nếu không có đối tượng nào có khoảng cách <= radius.
"""

import math

from ..ids import id_key


def nearest(pos, candidates, radius):
    best = None
    best_key = None
    for rank, obj in candidates:
        dist = math.dist(pos, obj["pos"])
        if dist <= radius:
            key = (dist, rank, id_key(obj["id"]))
            if best_key is None or key < best_key:
                best_key = key
                best = (rank, obj)
    return best
