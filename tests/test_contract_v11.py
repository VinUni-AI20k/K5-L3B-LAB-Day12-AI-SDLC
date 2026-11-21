"""P2-02: game.contract.json v1.1 (Ticket-02 mục 1, 2, 4.1): số chuẩn, ràng buộc mới, tương thích v1.0.

Các số mong đợi ở đây chép từ Ticket-02 để KHÓA số chuẩn: đổi contract sai số thì test đỏ.
"""

import copy
import json
import os
import unittest

from helpers import ROOT

from chonoi.contract import load_contract, validate_tuning
from chonoi.errors import BadInput
from chonoi.inventory import validate_items

CONTRACT = load_contract()
T = CONTRACT["tuning"]
G, Q = T["gather"], T["quan"]


def bad(edit):
    t = copy.deepcopy(T)
    edit(t)
    try:
        validate_tuning(t)
    except BadInput as e:
        return e
    return None


class StandardNumbers(unittest.TestCase):
    def test_version_and_team(self):
        self.assertEqual(CONTRACT["contract_version"], "1.1")
        self.assertEqual(CONTRACT["team_size"], 4)

    def test_gather_core_numbers_unchanged_from_v10(self):
        self.assertEqual((G["duration_s"], G["bounds"]), (180, {"x": [0, 100], "d": [0, 30]}))
        self.assertEqual((G["dock_pos"], G["dock_radius"], G["start_pos"]), ([2, 0], 3, [2, 0]))
        self.assertEqual((G["swim_speed"], G["ramp_max_ticks"], G["surface_depth"]), (4.0, 6, 0.5))
        self.assertEqual((G["oxygen_max_s"], G["oxygen_refill_per_tick"], G["choke_interval_ticks"]), (30, 6, 60))
        self.assertEqual((G["hp_max"], G["hold_capacity"], G["interact_radius"], G["node_yield"], G["regrow_s"]),
                         (3, 12, 2.0, 1, 20))
        self.assertEqual((G["catch_radius"], G["catch_cooldown_s"]), (2.0, 0.5))

    def test_nodes_n1_to_n6(self):
        self.assertEqual([(n["id"], n["kind"], n["pos"]) for n in G["nodes"]], [
            ("N1", "bong_dien_dien", [12, 0]), ("N2", "bong_dien_dien", [28, 0]), ("N3", "bong_sung", [44, 0]),
            ("N4", "bong_sung", [60, 0]), ("N5", "keo_neo", [76, 0]), ("N6", "keo_neo", [90, 0])])

    def test_fish_yield_and_dynamics(self):
        self.assertEqual(G["fish_yield"], {"ca_linh": 3, "ca_loc": 1, "ca_keo": 2})
        self.assertEqual((G["fish_initial"], G["fish_max"]), (8, 12))
        self.assertEqual((G["fish_speed"], G["fish_turn_ticks"], G["fish_spawn_ticks"], G["fish_spawn_clearance"]),
                         (1.5, 120, 360, 1.0))
        self.assertEqual(G["fish_x"], [4, 96])
        self.assertEqual(G["fish_depths"], {"ca_linh": [3, 12], "ca_loc": [8, 20], "ca_keo": [22, 28]})
        self.assertEqual(G["fish_spawn_x"], [15, 30, 45, 60, 75, 90])
        self.assertEqual(G["fish_spawn_depths"], {"ca_linh": [5, 10], "ca_loc": [10, 16], "ca_keo": [24, 27]})
        self.assertEqual(G["fish_weights"], {"ca_linh": 0.4, "ca_loc": 0.3, "ca_keo": 0.3})

    def test_spawn_points_are_36_pairs(self):
        pairs = {(k, x, d) for k, ds in G["fish_spawn_depths"].items() for x in G["fish_spawn_x"] for d in ds}
        self.assertEqual(len(pairs), 36)

    def test_crocodile_numbers(self):
        m = G["monsters"]
        self.assertEqual(m["species"]["ca_sau"], {
            "patrol_speed": 1.0, "chase_speed": 3.0, "detect_radius": 10, "exit_radius": 16, "depths": [10, 30],
            "hit_radius": 1.5, "recoil_ticks": 60, "recoil_dist": 2})
        self.assertEqual((m["invuln_ticks"], m["loss_ratio"]), (90, 0.5))
        self.assertEqual([(s["id"], s["pos"], s["waypoints"], s["from_day"]) for s in m["spawns"]], [
            ("M1", [68, 24], [[68, 24], [64, 24]], 1), ("M2", [85, 18], [[85, 18], [89, 18]], 3)])

    def test_quan_layout_and_rules(self):
        self.assertEqual([(s["id"], s["pos"]) for s in Q["stoves"]], [("B1", [2, 8]), ("B2", [5, 8])])
        self.assertEqual([(t["id"], t["pos"]) for t in Q["tables"]],
                         [("T1", [9, 2]), ("T2", [13, 2]), ("T3", [9, 6]), ("T4", [13, 6])])
        self.assertEqual((Q["bounds"], Q["start_pos"], Q["walk_speed"], Q["interact_radius"]),
                         ({"x": [0, 16], "z": [0, 10]}, [8, 5], 4.0, 1.5))
        self.assertEqual((Q["first_customer_tick"], Q["customer_interval_s"], Q["patience_s"], Q["eat_s"]),
                         (120, 15, 60, 10))
        self.assertEqual((Q["tip_rate"], Q["tip_min_patience_ratio"], Q["tip_reputation"], Q["left_reputation_delta"]),
                         (0.2, 0.5, 0.2, -0.5))
        self.assertEqual((Q["reputation_initial"], Q["reputation_min"], Q["reputation_max"], Q["burn_s"]),
                         (3.0, 0, 5, None))

    def test_menu_of_six_dishes(self):
        menu = T["menu"]
        self.assertEqual({k: (v["recipe"], v["cook_s"], v["price"]) for k, v in menu.items()}, {
            "ca_loc_nuong_trui": ({"ca_loc": 1}, 6, 60),
            "goi_bong_sung": ({"bong_sung": 2}, 4, 40),
            "lau_ca_linh_dien_dien": ({"ca_linh": 3, "bong_dien_dien": 1}, 10, 120),
            "canh_chua_ca_loc": ({"ca_loc": 1, "bong_dien_dien": 1}, 8, 90),
            "ca_keo_nuong": ({"ca_keo": 2}, 6, 70),
            "lau_mam": ({"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}, 12, 200)})

    def test_day_plan_d1_to_d5_slots(self):
        plan = T["day_plan"]
        self.assertEqual([d["day"] for d in plan], [1, 2, 3, 4, 5])
        self.assertEqual([sum(d["ingredients"].values()) for d in plan], [9, 10, 12, 9, 10])  # ô cần theo Ticket-02
        self.assertEqual(plan[0]["dishes"], {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3})
        self.assertEqual(plan[3]["dishes"], {"lau_mam": 1, "ca_loc_nuong_trui": 2, "goi_bong_sung": 1})

    def test_shop_upgrades(self):
        self.assertEqual(T["shop"]["max_ticks"], 600)
        self.assertEqual(T["shop"]["upgrades"]["oxygen"], [
            {"level": 1, "price": 200, "oxygen_max_s": 45}, {"level": 2, "price": 400, "oxygen_max_s": 60}])
        self.assertEqual(T["shop"]["upgrades"]["hp"], [
            {"level": 1, "price": 250, "hp_max": 4}, {"level": 2, "price": 500, "hp_max": 5}])

    def test_score_multiplier(self):
        self.assertEqual(T["score"], {"reputation_multiplier": 100})


class Validation(unittest.TestCase):
    def test_repo_contract_is_valid(self):
        validate_tuning(copy.deepcopy(T))

    def test_unsupported_version_rejected(self):
        with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
            data = json.load(f)
        data["contract_version"] = "2.0"
        path = os.path.join(os.environ.get("TEMP", "/tmp"), "contract-bad-version.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        try:
            with self.assertRaises(BadInput):
                load_contract(path)
        finally:
            os.remove(path)

    def test_fish_dynamics(self):
        self.assertIsNotNone(bad(lambda t: t["gather"].update(fish_initial=99)))  # vượt fish_max
        self.assertIsNotNone(bad(lambda t: t["gather"].update(fish_max=5)))  # fish_initial 8 > 5
        self.assertIsNotNone(bad(lambda t: t["gather"]["fish_weights"].pop("ca_keo")))
        self.assertIsNotNone(bad(lambda t: t["gather"]["fish_spawn_depths"].update(ca_keo=[1])))  # ngoài fish_depths
        self.assertIsNotNone(bad(lambda t: t["gather"].update(fish_spawn_x=[15, 15])))
        self.assertIsNotNone(bad(lambda t: t["gather"].update(fish_spawn_x=[1])))  # ngoài fish_x
        self.assertIsNotNone(bad(lambda t: t["gather"].update(fish_x=[96, 4])))
        self.assertIsNotNone(bad(lambda t: t["gather"].update(fish_turn_ticks=0)))

    def test_fish_initial_cannot_exceed_spawn_points(self):
        def edit(t):
            t["gather"]["fish_max"] = 100
            t["gather"]["fish_initial"] = 37
        self.assertIsNotNone(bad(edit))

    def test_nodes_and_fish_kinds(self):
        self.assertIsNotNone(bad(lambda t: t["gather"]["nodes"][0].update(kind="la_sen")))
        self.assertIsNotNone(bad(lambda t: t["gather"]["fish_yield"].update(ca_la=1)))
        self.assertIsNotNone(bad(lambda t: t["gather"]["nodes"].__setitem__(slice(None), [
            n for n in t["gather"]["nodes"] if n["kind"] != "bong_sung"])))

    def test_monsters(self):
        self.assertIsNotNone(bad(lambda t: t["gather"]["monsters"]["spawns"][0].update(waypoints=[[1, 1]])))
        self.assertIsNotNone(bad(lambda t: t["gather"]["monsters"]["spawns"][0].update(kind="ca_la")))
        self.assertIsNotNone(bad(lambda t: t["gather"]["monsters"]["spawns"][1].update(id="M1")))
        self.assertIsNotNone(bad(lambda t: t["gather"]["monsters"]["spawns"][1].update(from_day=9)))
        self.assertIsNotNone(bad(lambda t: t["gather"]["monsters"].update(loss_ratio=0)))
        self.assertIsNotNone(bad(lambda t: t["gather"]["monsters"]["species"]["ca_sau"].update(exit_radius=5)))
        self.assertIsNone(bad(lambda t: t["gather"].pop("monsters")))  # tùy chọn

    def test_day_plan_must_match_recipes(self):
        self.assertIsNotNone(bad(lambda t: t["day_plan"][0]["ingredients"].update(ca_loc=99)))
        self.assertIsNotNone(bad(lambda t: t["day_plan"][1]["dishes"].update(pho_bo=1)))
        self.assertIsNotNone(bad(lambda t: t["day_plan"].pop()))  # phải đúng 5 ngày
        self.assertIsNotNone(bad(lambda t: t["day_plan"][2].update(day=9)))
        self.assertIsNotNone(bad(lambda t: t["day_plan"][0]["dishes"].update(goi_bong_sung=0)))

    def test_shop_levels_must_increase(self):
        self.assertIsNotNone(bad(lambda t: t["shop"]["upgrades"]["oxygen"][1].update(oxygen_max_s=45)))
        self.assertIsNotNone(bad(lambda t: t["shop"]["upgrades"]["hp"][0].update(hp_max=3)))  # không hơn hp_max gốc
        self.assertIsNotNone(bad(lambda t: t["shop"]["upgrades"]["hp"][0].update(level=2)))
        self.assertIsNotNone(bad(lambda t: t["shop"].update(max_ticks=0)))
        self.assertIsNotNone(bad(lambda t: t["shop"]["upgrades"].pop("hp")))

    def test_v10_style_contract_still_valid(self):
        def to_v10(t):
            t["gather"]["fish_initial"] = [
                {"id": f"F{i}", "kind": "ca_loc", "pos": [10 * i, 5], "heading_deg": 0} for i in range(1, 7)]
            for key in ("fish_speed", "fish_turn_ticks", "fish_max", "fish_spawn_ticks", "fish_spawn_clearance",
                        "fish_x", "fish_depths", "fish_spawn_x", "fish_spawn_depths", "fish_weights", "monsters"):
                t["gather"].pop(key)
            t.pop("day_plan")
            t.pop("shop")
        self.assertIsNone(bad(to_v10))


class NewIngredients(unittest.TestCase):
    def test_inventory_accepts_ca_keo_and_keo_neo(self):
        self.assertEqual(validate_items({"ca_keo": 2, "keo_neo": 1, "ca_loc": 0}), {"ca_keo": 2, "keo_neo": 1})
        with self.assertRaises(BadInput):
            validate_items({"la_sen": 1})


if __name__ == "__main__":
    unittest.main()
