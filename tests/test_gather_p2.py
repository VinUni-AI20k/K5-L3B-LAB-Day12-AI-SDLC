"""Unit tests for GatherSim Phase 2 (TICKET-02: Contract v1.1).

Coverage:
- Kèo nèo N5, N6 harvesting & inventory
- Cá kèo (ca_keo) catching & yield = 2
- Đàn cá bơi, phản xạ mép x in [4, 96] và d in [d_min, d_max]
- Đổi hướng cá theo seed ở bước 120
- Sinh cá theo lịch ở phase_tick = 360*k (fish_spawned)
- Cá Sấu Năm Chèo M1/M2: patrol, chase khi d >= 10 và dist <= 10, thoát chase
- Cá Sấu cắn (hit): -1 Máu, rơi floor(hold/2) LIFO, bất tử 90 tick, quái recoil 60 tick (monster_hit)
- Ngất do quái: Máu về 0 -> faint cause "monster", rơi nốt phần giỏ còn lại, kho rỗng
"""

import math
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import LiveInputs
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim


def make_sim(scenario=None, seed=42):
    contract = load_contract()
    tuning = contract["tuning"]
    sc = scenario or {}
    streams = Streams(seed)
    ids = IdAllocator()
    return GatherSim(tuning, sc, streams, ids)


class TestGatherP2(unittest.TestCase):
    def test_keo_neo_harvesting(self):
        # N5 is at [76, 0] with kind keo_neo
        sim = make_sim({"player": {"pos": [76, 0]}, "hold": []})
        inp = LiveInputs()
        inp.set(interact=True)
        evs = sim.step(inp.advance())
        names = [e[0] for e in evs]
        self.assertIn("gather", names)
        g_data = next(e[1] for e in evs if e[0] == "gather")
        self.assertEqual(g_data["node_id"], "N5")
        self.assertEqual(g_data["kind"], "keo_neo")
        self.assertEqual(g_data["amount"], 1)
        self.assertEqual(sim.hold, ["keo_neo"])
        self.assertEqual(sim.inventory_items(), {"keo_neo": 1})

    def test_ca_keo_catching(self):
        # Place player near a ca_keo fish at [30, 25] (underwater d=25)
        fish = [{"id": "F1", "kind": "ca_keo", "pos": [30, 25]}]
        sim = make_sim({"player": {"pos": [30, 25]}, "hold": [], "fish": fish, "random_fish": False})
        inp = LiveInputs()
        inp.set(catch=True)
        evs = sim.step(inp.advance())
        names = [e[0] for e in evs]
        self.assertIn("fish_caught", names)
        fc_data = next(e[1] for e in evs if e[0] == "fish_caught")
        self.assertEqual(fc_data["fish_id"], "F1")
        self.assertEqual(fc_data["kind"], "ca_keo")
        self.assertEqual(fc_data["yield"], 2)
        self.assertEqual(sim.hold, ["ca_keo", "ca_keo"])
        self.assertEqual(sim.catch_cd_ticks, 30)

    def test_fish_swimming_and_edge_reflection(self):
        # Place ca_linh near right edge [95.99, 5] moving right (heading_deg = 0)
        # ca_linh x bounds [4, 96], speed 1.5 m/s = 0.025 m/tick
        # After 1 step: 95.99 + 0.025 = 96.015 > 96 -> bounces to 96 - 0.015 = 95.985
        # Heading deg inverts vx: 0 deg -> 180 deg
        fish = [{"id": "F1", "kind": "ca_linh", "pos": [95.99, 5.0], "heading_deg": 0.0, "age_ticks": 0}]
        sim = make_sim({"player": {"pos": [2, 0]}, "fish": fish, "random_fish": True})
        inp = LiveInputs()
        sim.step(inp.advance())
        f = sim.fish[0]
        self.assertLessEqual(f["pos"][0], 96.0)
        self.assertAlmostEqual(f["pos"][0], 95.985, places=3)
        self.assertAlmostEqual(f["heading_deg"], 180.0, places=1)
        self.assertEqual(f["age_ticks"], 1)

    def test_fish_turn_at_120_ticks(self):
        # Fish moves 119 ticks with heading 0.0
        fish = [{"id": "F1", "kind": "ca_linh", "pos": [50.0, 5.0], "heading_deg": 0.0, "age_ticks": 119}]
        sim = make_sim({"player": {"pos": [2, 0]}, "fish": fish, "random_fish": True}, seed=10)
        inp = LiveInputs()
        sim.step(inp.advance())
        f = sim.fish[0]
        self.assertEqual(f["age_ticks"], 120)
        # Heading should have been randomized at tick 120
        self.assertNotEqual(f["heading_deg"], 0.0)

    def test_periodic_fish_spawn(self):
        # At phase_tick = 359, next step phase_tick becomes 360 -> triggers spawn
        sim = make_sim({"player": {"pos": [2, 0]}, "phase_tick": 359, "fish": [
            {"id": "F1", "kind": "ca_linh", "pos": [15, 5], "heading_deg": 0.0, "age_ticks": 10}
        ], "random_fish": True}, seed=7)
        inp = LiveInputs()
        evs = sim.step(inp.advance())
        names = [e[0] for e in evs]
        self.assertIn("fish_spawned", names)
        sp_data = next(e[1] for e in evs if e[0] == "fish_spawned")
        self.assertEqual(sp_data["id"], "F2")
        self.assertIn(sp_data["kind"], ("ca_linh", "ca_loc", "ca_keo"))
        self.assertEqual(len(sim.fish), 2)
        # New fish has age_ticks = 0
        new_fish = next(f for f in sim.fish if f["id"] == "F2")
        self.assertEqual(new_fish["age_ticks"], 0)

    def test_monster_patrol_and_chase(self):
        # M1 starts at [60, 24] with target waypoint [64, 24]
        # Player at [2, 0] (surface) -> M1 stays in patrol
        sim = make_sim({"player": {"pos": [2, 0]}})
        m1 = sim.monsters[0]
        self.assertEqual(m1["state"], "patrol")
        inp = LiveInputs()
        # Step 60 ticks (1 sec): patrol speed 1.0 m/s -> moves 1.0 m towards [64, 24]
        for _ in range(60):
            sim.step(inp.advance())
        self.assertAlmostEqual(m1["pos"][0], 61.0, places=2)
        self.assertAlmostEqual(m1["pos"][1], 24.0, places=2)

        # Move player to [61.0, 15.0] (d=15 >= 10, dist = 9.0 <= 10.0)
        sim.pos = [61.0, 15.0]
        sim.step(inp.advance())
        # M1 detects player and enters chase
        self.assertEqual(m1["state"], "chase")
        # In chase, speed is 3.0 m/s (moves upward towards player d=15)
        self.assertLess(m1["pos"][1], 24.0)

    def test_monster_chase_exit(self):
        # M1 in chase at [60, 20], player swims to surface d=0.4 (< 10)
        sim = make_sim({"player": {"pos": [60, 0.4]}, "monsters": [
            {"id": "M1", "kind": "ca_sau", "pos": [60, 20], "waypoints": [[60, 24], [64, 24]],
             "target_idx": 1, "state": "chase", "state_ticks_left": 0, "recoil_dir": None}
        ]})
        inp = LiveInputs()
        sim.step(inp.advance())
        m1 = sim.monsters[0]
        # Since player d < 10, monster exits chase and returns to patrol!
        self.assertEqual(m1["state"], "patrol")

    def test_monster_hit_and_recoil_and_drop_lifo(self):
        # Player at [60, 20] (d=20 >= 10) with 5 items in hold, hp=3, invuln=0
        # M1 at [60, 21] (dist = 1.0 <= 1.5)
        hold_items = ["ca_loc", "bong_sung", "ca_linh", "keo_neo", "ca_keo"]
        sim = make_sim({
            "player": {"pos": [60, 20], "hp": 3, "invuln_ticks": 0},
            "hold": list(hold_items),
            "monsters": [
                {"id": "M1", "kind": "ca_sau", "pos": [60, 21], "waypoints": [[60, 24], [64, 24]],
                 "target_idx": 1, "state": "patrol", "state_ticks_left": 0, "recoil_dir": None}
            ]
        })
        inp = LiveInputs()
        evs = sim.step(inp.advance())
        names = [e[0] for e in evs]
        self.assertIn("monster_hit", names)
        hit_data = next(e[1] for e in evs if e[0] == "monster_hit")
        self.assertEqual(hit_data["monster_id"], "M1")
        self.assertEqual(hit_data["hp"], 2)
        # Drop floor(5/2) = 2 items LIFO: last 2 items were "ca_keo", then "keo_neo"
        self.assertEqual(hit_data["lost"], ["ca_keo", "keo_neo"])
        self.assertEqual(sim.hold, ["ca_loc", "bong_sung", "ca_linh"])
        # Player invulnerable for 90 ticks (decremented to 89 at end of next step or 90 during hit)
        self.assertEqual(sim.invuln_ticks, 90)
        # M1 entered recoil with timer 60
        m1 = sim.monsters[0]
        self.assertEqual(m1["state"], "recoil")
        self.assertEqual(m1["state_ticks_left"], 60)
        self.assertIsNotNone(m1["recoil_dir"])

    def test_monster_kill_and_faint(self):
        # Player at hp=1 touched by M1 -> Máu becomes 0 -> faint with cause "monster"
        sim = make_sim({
            "player": {"pos": [60, 20], "hp": 1, "invuln_ticks": 0},
            "hold": ["ca_loc", "bong_sung"],
            "monsters": [
                {"id": "M1", "kind": "ca_sau", "pos": [60, 20.5], "waypoints": [[60, 24], [64, 24]],
                 "target_idx": 1, "state": "patrol", "state_ticks_left": 0, "recoil_dir": None}
            ]
        })
        inp = LiveInputs()
        evs = sim.step(inp.advance())
        names = [e[0] for e in evs]
        self.assertIn("monster_hit", names)
        self.assertIn("faint", names)
        self.assertIn("gather_end", names)
        self.assertTrue(sim.done)
        self.assertEqual(sim.reason, "fainted")
        faint_data = next(e[1] for e in evs if e[0] == "faint")
        self.assertEqual(faint_data["cause"], "monster")
        self.assertEqual(faint_data["hp"], 0)
        self.assertEqual(sim.inventory_items(), {})


if __name__ == "__main__":
    unittest.main()
