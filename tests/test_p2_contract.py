"""Kiểm game.contract.json theo Test Contract v1.1 (Phase 2, TICKET-02 mục 1, 2, 4.1). Vai: QA.

Chỉ chạy khi contract_version = "1.1" (xem rules_common.requires_v11). Số chuẩn lấy từ Phase2.md; test này là
"phép thử bàn giao": Integrator đổi contract sang 1.1 thì các điều dưới đây phải đúng.

| AC        | Nhóm test | Nội dung (Phase2.md)                                                  |
|-----------|-----------|-----------------------------------------------------------------------|
| AC-P2-01  | Gather    | mục 1.1: 8 đàn ban đầu, nút N1–N6, yield 3 loài, khóa cá bơi/sinh     |
| AC-P2-02  | Monster   | mục 1.2: Cá Sấu M1/M2, bất tử 90, bỏ một nửa giỏ                       |
| AC-P2-03  | Quan      | mục 1.3: B1–B2, T1–T4, 6 món đúng công thức/thời gian/giá             |
| AC-P2-04  | DayShop   | mục 2: day_plan D1–D5 khớp tổng công thức, nâng cấp oxy/hp, shop      |

Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -p "test_p2_contract.py" -v
"""

import unittest

from rules_common import contract_all, requires_v11

MENU = {  # id: (công thức, giây nấu, giá) — Phase2.md mục 1.3
    "ca_loc_nuong_trui": ({"ca_loc": 1}, 6, 60),
    "goi_bong_sung": ({"bong_sung": 2}, 4, 40),
    "lau_ca_linh_dien_dien": ({"ca_linh": 3, "bong_dien_dien": 1}, 10, 120),
    "canh_chua_ca_loc": ({"ca_loc": 1, "bong_dien_dien": 1}, 8, 90),
    "ca_keo_nuong": ({"ca_keo": 2}, 6, 70),
    "lau_mam": ({"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}, 12, 200),
}
# Phase2.md mục 2: món và số suất kế hoạch từng Ngày, và nguyên liệu cần.
PLAN = {
    1: ({"ca_loc_nuong_trui": 3, "goi_bong_sung": 3}, {"ca_loc": 3, "bong_sung": 6}),
    2: ({"ca_loc_nuong_trui": 2, "lau_ca_linh_dien_dien": 2}, {"ca_loc": 2, "ca_linh": 6, "bong_dien_dien": 2}),
    3: ({"goi_bong_sung": 2, "canh_chua_ca_loc": 2, "ca_keo_nuong": 2},
        {"bong_sung": 4, "ca_loc": 2, "bong_dien_dien": 2, "ca_keo": 4}),
    4: ({"lau_mam": 1, "ca_loc_nuong_trui": 2, "goi_bong_sung": 1},
        {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1, "ca_loc": 2, "bong_sung": 2}),
    5: ({"lau_mam": 1, "lau_ca_linh_dien_dien": 1, "ca_loc_nuong_trui": 1},
        {"ca_linh": 5, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 2, "ca_loc": 1}),
}


def total(dishes):
    out = {}
    for dish, n in dishes.items():
        for kind, q in MENU[dish][0].items():
            out[kind] = out.get(kind, 0) + q * n
    return out


@requires_v11
class Gather(unittest.TestCase):
    """AC-P2-01 — số chuẩn buổi sáng."""

    def setUp(self):
        self.c = contract_all()
        self.g = self.c["tuning"]["gather"]

    def test_gather_01_fish_initial_is_8(self):
        """`fish_initial` có đúng 8 đàn, id khác nhau, đủ cả ba loài."""
        fish = self.g["fish_initial"]
        self.assertEqual(len(fish), 8)
        self.assertEqual(len({f["id"] for f in fish}), 8)
        self.assertEqual({f["kind"] for f in fish}, {"ca_linh", "ca_loc", "ca_keo"})

    def test_gather_02_six_nodes_two_per_plant(self):
        """6 nút: N1–N2 điên điển, N3–N4 bông súng, N5–N6 kèo nèo, đúng tọa độ, d = 0."""
        want = {"N1": ("bong_dien_dien", [12, 0]), "N2": ("bong_dien_dien", [28, 0]),
                "N3": ("bong_sung", [44, 0]), "N4": ("bong_sung", [60, 0]),
                "N5": ("keo_neo", [76, 0]), "N6": ("keo_neo", [90, 0])}
        got = {n["id"]: (n["kind"], n["pos"]) for n in self.g["nodes"]}
        self.assertEqual(got, want)

    def test_gather_03_fish_yield_three_species(self):
        self.assertEqual(self.g["fish_yield"], {"ca_linh": 3, "ca_loc": 1, "ca_keo": 2})

    def test_gather_04_fish_swim_and_spawn_keys_present(self):
        """Các khóa cá bơi/sinh có mặt (giá trị chi tiết do luật và test hành vi kiểm)."""
        for key in ("fish_speed", "fish_turn_ticks", "fish_max", "fish_spawn_ticks", "fish_spawn_clearance",
                    "fish_x", "fish_depths", "fish_spawn_x", "fish_spawn_depths", "fish_weights"):
            self.assertIn(key, self.g, key)
        self.assertEqual(self.g["fish_max"], 12)
        self.assertEqual(self.g["fish_turn_ticks"], 120)
        self.assertEqual(self.g["fish_spawn_ticks"], 360)
        self.assertEqual(self.g["fish_spawn_x"], [15, 30, 45, 60, 75, 90])

    def test_gather_05_nodes_and_fish_spawn_inside_bounds(self):
        b = self.g["bounds"]
        for e in self.g["nodes"] + self.g["fish_initial"]:
            self.assertTrue(b["x"][0] <= e["pos"][0] <= b["x"][1] and b["d"][0] <= e["pos"][1] <= b["d"][1], e)
        self.assertTrue(all(f["pos"][1] > self.g["surface_depth"] for f in self.g["fish_initial"]))


@requires_v11
class Monster(unittest.TestCase):
    """AC-P2-02 — Cá Sấu Năm Chèo."""

    def setUp(self):
        self.m = contract_all()["tuning"]["gather"]["monsters"]

    def test_monster_01_global_rules(self):
        self.assertEqual(self.m["invuln_ticks"], 90)
        self.assertEqual(self.m["loss_ratio"], 0.5)

    def test_monster_02_ca_sau_species(self):
        s = self.m["species"]["ca_sau"]
        for key in ("patrol_speed", "chase_speed", "detect_radius", "exit_radius", "depths", "hit_radius",
                    "recoil_ticks", "recoil_dist"):
            self.assertIn(key, s, key)
        self.assertEqual((s["patrol_speed"], s["chase_speed"]), (1.0, 3.0))
        self.assertEqual((s["detect_radius"], s["exit_radius"], s["hit_radius"]), (10, 16, 1.5))
        self.assertEqual(s["recoil_ticks"], 60)
        self.assertEqual(s["depths"], [10, 30])

    def test_monster_03_spawns_m1_day1_m2_day3(self):
        sp = {m["id"]: m for m in self.m["spawns"]}
        self.assertEqual(sp["M1"]["waypoints"], [[60, 24], [64, 24]])
        self.assertEqual(sp["M1"]["from_day"], 1)
        self.assertEqual(sp["M2"]["waypoints"], [[85, 18], [89, 18]])
        self.assertEqual(sp["M2"]["from_day"], 3)
        self.assertEqual(sp["M1"]["pos"], sp["M1"]["waypoints"][0], "waypoint đầu là vị trí xuất phát")


@requires_v11
class Quan(unittest.TestCase):
    """AC-P2-03 — quán 2 bếp, 4 bàn, 6 món."""

    def setUp(self):
        self.t = contract_all()["tuning"]

    def test_quan_01_stoves_and_tables(self):
        q = self.t["quan"]
        self.assertEqual({s["id"]: s["pos"] for s in q["stoves"]}, {"B1": [2, 8], "B2": [5, 8]})
        self.assertEqual({s["id"]: s["pos"] for s in q["tables"]},
                         {"T1": [9, 2], "T2": [13, 2], "T3": [9, 6], "T4": [13, 6]})

    def test_quan_02_menu_matches_ticket(self):
        menu = self.t["menu"]
        self.assertEqual(set(menu), set(MENU))
        for dish, (recipe, cook_s, price) in MENU.items():
            self.assertEqual(menu[dish]["recipe"], recipe, dish)
            self.assertEqual(menu[dish]["cook_s"], cook_s, dish)
            self.assertEqual(menu[dish]["price"], price, dish)

    def test_quan_03_customer_schedule(self):
        """Lượt đầu tick 120, chu kỳ 900 tick (15 s), kiên nhẫn 60 s, ăn 10 s, boa 0.2 / ngưỡng 0.5."""
        q = self.t["quan"]
        self.assertEqual((q["first_customer_tick"], q["customer_interval_s"] * 60), (120, 900))
        self.assertEqual((q["patience_s"], q["eat_s"]), (60, 10))
        self.assertEqual((q["tip_rate"], q["tip_min_patience_ratio"], q["tip_reputation"]), (0.2, 0.5, 0.2))


@requires_v11
class DayShop(unittest.TestCase):
    """AC-P2-04 — kế hoạch ngày và Shop."""

    def setUp(self):
        self.t = contract_all()["tuning"]

    def test_day_01_plan_has_five_days_matching_ticket(self):
        plan = {p["day"]: p for p in self.t["day_plan"]}
        self.assertEqual(sorted(plan), [1, 2, 3, 4, 5])
        for day, (dishes, ingredients) in PLAN.items():
            self.assertEqual(plan[day]["dishes"], dishes, f"D{day} dishes")
            self.assertEqual(plan[day]["ingredients"], ingredients, f"D{day} ingredients")

    def test_day_02_plan_ingredients_equal_sum_of_recipes(self):
        """ingredients = tổng (công thức × số suất) — kiểm bằng menu trong contract, không bằng bảng trong test."""
        menu = self.t["menu"]
        for p in self.t["day_plan"]:
            want = {}
            for dish, n in p["dishes"].items():
                for kind, q in menu[dish]["recipe"].items():
                    want[kind] = want.get(kind, 0) + q * n
            self.assertEqual(p["ingredients"], want, f"D{p['day']}")

    def test_shop_01_upgrades_and_timeout(self):
        shop = self.t["shop"]
        self.assertEqual(shop["max_ticks"], 600)
        ox = {u["level"]: (u["price"], u["oxygen_max_s"]) for u in shop["upgrades"]["oxygen"]}
        hp = {u["level"]: (u["price"], u["hp_max"]) for u in shop["upgrades"]["hp"]}
        self.assertEqual(ox, {1: (200, 45), 2: (400, 60)})
        self.assertEqual(hp, {1: (250, 4), 2: (500, 5)})

    def test_contract_version_and_commands(self):
        c = contract_all()
        self.assertIn(c["contract_version"], ("1.1", "1.2", "1.3"))   # P3 lên 1.2, P4 lên 1.3; số chuẩn P2 vẫn phải đúng
        for key in ("build_cmd", "run_cmd", "headless_cmd"):
            self.assertTrue(c[key])


if __name__ == "__main__":
    unittest.main()
