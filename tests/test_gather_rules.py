"""P1-09: luật gather (oxy, ngạt, ngất, giỏ, hái, bắt cá, cập bến).

Bổ sung cho tests/test_gather_prd.py (kiểm payload sự kiện): file này kiểm HÀNH VI theo từng luật.
Mọi số (oxy, bán kính, hồi chiêu, sức chứa...) đọc từ game.contract.json, không viết cứng.
Chạy trong tiến trình qua Session để nhanh; tất định và lỗi mã 2 đã có ở các test headless khác.
"""

import math
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer
from chonoi.runner import Session

T = load_contract()["tuning"]
G = T["gather"]
HZ = T["tick_hz"]
DOCK = G["dock_pos"]
FAR = 20  # x xa bến (bến ở [2, 0], bán kính 3) và xa các nút/đàn mặc định; scenario tự đặt nút, cá


def run(scenario, frames=(), ticks=1):
    """Chạy `ticks` bước (dừng sớm nếu kết thúc). Trả (session, danh sách dòng sự kiện)."""
    sess = Session("gather", T, scenario, 1)
    player = InputPlayer(list(frames))
    rows = []
    while sess.tick < ticks and not sess.done:
        rows.extend(sess.step(player.advance(sess.tick)))
    return sess, rows


def named(rows, name):
    return [r for r in rows if r["name"] == name]


def node(ident, x, d=0, kind="bong_sung"):
    return {"id": ident, "kind": kind, "pos": [x, d]}


def fish(ident, x, d, kind="ca_linh"):
    return {"id": ident, "kind": kind, "pos": [x, d]}


class Oxygen(unittest.TestCase):
    def test_underwater_drains_one_per_tick(self):
        sess, _ = run({"player": {"pos": [FAR, 5]}}, ticks=10)
        self.assertEqual(sess.sim.oxygen_ticks, sess.sim.oxygen_max - 10)

    def test_surface_refills_and_caps_at_max(self):
        start = sess_max = round(G["oxygen_max_s"] * HZ)
        refill = G["oxygen_refill_per_tick"]
        sess, _ = run({"player": {"pos": [FAR, 0], "oxygen_ticks": start - 100}}, ticks=1)
        self.assertEqual(sess.sim.oxygen_ticks, start - 100 + refill)
        sess, _ = run({"player": {"pos": [FAR, 0], "oxygen_ticks": start - 100}}, ticks=math.ceil(100 / refill) + 5)
        self.assertEqual(sess.sim.oxygen_ticks, sess_max)

    def test_dive_then_surface_events_once_each(self):
        frames = [{"tick": 0, "move": [0, 1]}, {"tick": 40, "move": [0, -1]}]
        sess, rows = run({"player": {"pos": [FAR, 0.4]}}, frames, ticks=150)
        order = [r["name"] for r in rows if r["name"] in ("dive", "surface")]
        self.assertEqual(order, ["dive", "surface"])
        for r in rows:
            if r["name"] in ("dive", "surface"):
                self.assertEqual(len(r["data"]["pos"]), 2)
        self.assertTrue(sess.sim._at_surface())

    def test_oxygen_empty_fires_once_when_reaching_zero(self):
        sess, rows = run({"player": {"pos": [FAR, 5], "oxygen_ticks": 3}}, ticks=20)
        empties = named(rows, "oxygen_empty")
        self.assertEqual([r["tick"] for r in empties], [3])
        self.assertEqual(sess.sim.oxygen_ticks, 0)


class Choking(unittest.TestCase):
    def test_choke_every_interval_costs_one_hp(self):
        every = G["choke_interval_ticks"]
        sess, rows = run({"player": {"pos": [FAR, 5], "oxygen_ticks": 1, "hp": G["hp_max"]}}, ticks=2 * every + 5)
        chokes = named(rows, "choke")
        self.assertEqual([(r["tick"], r["data"]["hp"]) for r in chokes],
                         [(every, G["hp_max"] - 1), (2 * every, G["hp_max"] - 2)])
        self.assertEqual(named(rows, "faint"), [])
        self.assertFalse(sess.done)

    def test_surfacing_resets_choke_counter(self):
        scenario = {"player": {"pos": [FAR, 1.0], "oxygen_ticks": 0, "zero_oxy_ticks": 30, "hp": G["hp_max"]}}
        sess, rows = run(scenario, [{"tick": 0, "move": [0, -1]}], ticks=40)
        self.assertEqual(named(rows, "choke"), [])
        self.assertEqual(sess.sim.zero_oxy_ticks, 0)
        self.assertGreater(sess.sim.oxygen_ticks, 0)
        self.assertEqual(sess.sim.hp, G["hp_max"])

    def test_faint_with_empty_hold_reports_nothing_lost(self):
        sess, rows = run({"player": {"pos": [FAR, 5], "oxygen_ticks": 1, "hp": 1}, "hold": []},
                         ticks=G["choke_interval_ticks"])
        self.assertEqual(named(rows, "faint")[0]["data"]["lost"], [])
        self.assertTrue(sess.done)
        self.assertEqual(sess.sim.reason, "fainted")

    def test_faint_ends_the_session_with_empty_inventory(self):
        hold = ["ca_loc", "bong_sung"]
        sess, rows = run({"player": {"pos": [FAR, 5], "oxygen_ticks": 1, "hp": 1}, "hold": hold},
                         ticks=G["choke_interval_ticks"] + 50)
        self.assertEqual(sess.tick, G["choke_interval_ticks"])  # dừng ngay tại tick ngất
        self.assertEqual(named(rows, "faint")[0]["data"]["lost"], hold[::-1])  # món nhặt sau rơi trước (LIFO)
        end = named(rows, "gather_end")[0]["data"]
        self.assertEqual(end, {"reason": "fainted", "inventory": {"items": {}}})
        self.assertEqual(sess.sim.inventory_items(), {})


class Dock(unittest.TestCase):
    def test_dock_ends_with_hold_as_inventory(self):
        hold = ["ca_loc", "bong_sung", "ca_loc"]
        sess, rows = run({"player": {"pos": list(DOCK)}, "hold": hold}, [{"tick": 0, "interact": True}], ticks=5)
        end = named(rows, "gather_end")[0]["data"]
        self.assertEqual(end, {"reason": "docked", "inventory": {"items": {"bong_sung": 1, "ca_loc": 2}}})
        self.assertEqual(sess.tick, 1)

    def test_dock_wins_over_harvest_in_same_press(self):
        scenario = {"player": {"pos": list(DOCK)}, "nodes": [node("N1", DOCK[0] + 1)]}
        sess, rows = run(scenario, [{"tick": 0, "interact": True}], ticks=3)
        self.assertEqual([r["name"] for r in rows], ["gather_end"])
        self.assertTrue(sess.sim.nodes[0]["regrow_ticks"] == 0)

    def test_interact_outside_dock_does_not_end(self):
        sess, rows = run({"player": {"pos": [FAR, 0]}, "nodes": []}, [{"tick": 0, "interact": True}], ticks=3)
        self.assertFalse(sess.done)
        self.assertEqual(rows, [])


class Harvest(unittest.TestCase):
    def test_not_underwater(self):
        r = G["interact_radius"]
        sess, rows = run({"player": {"pos": [FAR, r]}, "nodes": [node("N1", FAR)]}, [{"tick": 0, "interact": True}])
        self.assertEqual(named(rows, "gather"), [])
        self.assertEqual(sess.sim.hold, [])

    def test_at_surface_within_radius_gathers_node_yield(self):
        sess, rows = run({"player": {"pos": [FAR, 0.4]}, "nodes": [node("N1", FAR)]}, [{"tick": 0, "interact": True}])
        self.assertEqual(len(named(rows, "gather")), 1)
        self.assertEqual(sess.sim.hold, ["bong_sung"] * G["node_yield"])

    def test_out_of_range(self):
        far = G["interact_radius"] + 0.5
        sess, rows = run({"player": {"pos": [FAR, 0]}, "nodes": [node("N1", FAR + far)]}, [{"tick": 0, "interact": True}])
        self.assertEqual(named(rows, "gather"), [])
        self.assertEqual(sess.sim.hold, [])

    def test_held_key_gathers_only_once(self):
        # hai nút cùng chỗ: nếu giữ phím tự lặp thì N2 cũng bị hái
        scenario = {"player": {"pos": [FAR, 0]}, "nodes": [node("N1", FAR), node("N2", FAR)]}
        _, rows = run(scenario, [{"tick": 0, "interact": True}], ticks=10)
        self.assertEqual([r["data"]["node_id"] for r in named(rows, "gather")], ["N1"])

    def test_node_regrows_after_regrow_time_and_can_be_gathered_again(self):
        regrow = round(G["regrow_s"] * HZ)
        frames = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False}, {"tick": 2, "interact": True},
                  {"tick": 3, "interact": False}, {"tick": regrow + 5, "interact": True}]
        sess, rows = run({"player": {"pos": [FAR, 0]}, "nodes": [node("N1", FAR)]}, frames, ticks=regrow + 10)
        gathers = named(rows, "gather")
        self.assertEqual(len(gathers), 2)  # lần bấm lúc đang mọc lại bị bỏ qua
        self.assertEqual(gathers[0]["tick"], 1)
        regrown = named(rows, "node_regrown")
        self.assertEqual([r["tick"] for r in regrown], [1 + regrow])
        self.assertEqual(gathers[1]["tick"], regrow + 6)

    def test_nodes_not_ready_are_skipped_for_the_next_nearest(self):
        scenario = {"player": {"pos": [FAR, 0]},
                    "nodes": [dict(node("N1", FAR), regrow_ticks=100), node("N2", FAR + 1)]}
        _, rows = run(scenario, [{"tick": 0, "interact": True}])
        self.assertEqual([r["data"]["node_id"] for r in named(rows, "gather")], ["N2"])


class Catching(unittest.TestCase):
    def test_not_at_surface(self):
        sess, rows = run({"player": {"pos": [FAR, 0.3]}, "fish": [fish("F1", FAR, 1.5)]}, [{"tick": 0, "catch": True}])
        self.assertEqual(named(rows, "fish_caught"), [])
        self.assertEqual(len(sess.sim.fish), 1)

    def test_out_of_range(self):
        far = G["catch_radius"] + 0.5
        sess, rows = run({"player": {"pos": [FAR, 5]}, "fish": [fish("F1", FAR, 5 + far)]}, [{"tick": 0, "catch": True}])
        self.assertEqual(named(rows, "fish_caught"), [])
        self.assertEqual(len(sess.sim.fish), 1)

    def test_catch_adds_yield_to_end_of_hold_and_removes_shoal(self):
        sess, rows = run({"player": {"pos": [FAR, 5]}, "fish": [fish("F1", FAR, 6)], "hold": ["bong_sung"]},
                         [{"tick": 0, "catch": True}])
        self.assertEqual(sess.sim.hold, ["bong_sung"] + ["ca_linh"] * G["fish_yield"]["ca_linh"])
        self.assertEqual(sess.sim.fish, [])

    def test_loc_and_linh_have_their_own_yield(self):
        for kind in ("ca_linh", "ca_loc"):
            sess, _ = run({"player": {"pos": [FAR, 5]}, "fish": [fish("F1", FAR, 6, kind)]}, [{"tick": 0, "catch": True}])
            self.assertEqual(sess.sim.hold, [kind] * G["fish_yield"][kind], kind)

    def test_cooldown_blocks_until_it_expires(self):
        cd = round(G["catch_cooldown_s"] * HZ)
        scenario = {"player": {"pos": [FAR, 5]}, "fish": [fish("F1", FAR, 6), fish("F2", FAR, 6.5)]}

        def second_press_at(t):
            frames = [{"tick": 0, "catch": True}, {"tick": 1, "catch": False}, {"tick": t, "catch": True}]
            _, rows = run(scenario, frames, ticks=t + 2)
            return [r["data"]["fish_id"] for r in named(rows, "fish_caught")]

        self.assertEqual(second_press_at(cd - 1), ["F1"])
        self.assertEqual(second_press_at(cd), ["F1", "F2"])

    def test_failed_catch_does_not_start_cooldown(self):
        frames = [{"tick": 0, "catch": True}, {"tick": 1, "catch": False}, {"tick": 2, "catch": True}]
        scenario = {"player": {"pos": [FAR, 5]}, "fish": [fish("F1", FAR, 5 + G["catch_radius"] + 1)]}
        sess, rows = run(scenario, frames, ticks=3)
        self.assertEqual(sess.sim.catch_cd_ticks, 0)
        self.assertEqual(named(rows, "fish_caught"), [])

    def test_full_hold_keeps_shoal_and_does_not_start_cooldown(self):
        hold = ["bong_sung"] * (G["hold_capacity"] - 1)
        sess, rows = run({"player": {"pos": [FAR, 5]}, "fish": [fish("F1", FAR, 6)], "hold": hold},
                         [{"tick": 0, "catch": True}])
        self.assertEqual(len(named(rows, "hold_full")), 1)
        self.assertEqual(len(sess.sim.fish), 1)
        self.assertEqual(sess.sim.hold, hold)
        self.assertEqual(sess.sim.catch_cd_ticks, 0)


class Hold(unittest.TestCase):
    def test_capacity_is_never_exceeded(self):
        cap = G["hold_capacity"]
        nodes = [node(f"N{i}", FAR) for i in range(1, cap + 3)]
        frames = []
        for k in range(cap + 2):
            frames += [{"tick": 2 * k, "interact": True}, {"tick": 2 * k + 1, "interact": False}]
        sess, rows = run({"player": {"pos": [FAR, 0]}, "nodes": nodes}, frames, ticks=2 * cap + 6)
        self.assertEqual(len(sess.sim.hold), cap)
        self.assertEqual(len(named(rows, "gather")), cap)
        self.assertEqual(len(named(rows, "hold_full")), 2)


if __name__ == "__main__":
    unittest.main()
