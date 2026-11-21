import json
import unittest
from pathlib import Path

from chonoi.sim.gather import GatherSim
from chonoi.ids import IdAllocator
from chonoi.rng import Streams


ROOT = Path(__file__).resolve().parents[1]
with (ROOT / "game.contract.json").open(encoding="utf-8") as f:
    TUNING = json.load(f)["tuning"]


class TestInput:
    def __init__(self, move=(0.0, 0.0), buttons=()):
        self.move = move
        self.buttons = set(buttons)

    def pressed(self, name):
        return name in self.buttons


def make_sim(scenario=None):
    return GatherSim(
        TUNING, scenario or {}, Streams(1), IdAllocator()
    )


def tick(sim, buttons=(), move=(0.0, 0.0)):
    return sim.step(TestInput(move, buttons))


def has_event(events, name):
    return any(event == name for event, _ in events)


class GatherPhase1Tests(unittest.TestCase):

    def test_01_oxygen_decreases_underwater(self):
        s = make_sim({"player": {
            "pos": [20, 5], "oxygen_ticks": 10
        }})
        tick(s)
        self.assertEqual(s.oxygen_ticks, 9)

    def test_02_oxygen_refills_at_surface(self):
        s = make_sim({"player": {
            "pos": [20, 0], "oxygen_ticks": 10
        }})
        tick(s)
        self.assertEqual(s.oxygen_ticks, 16)

    def test_03_oxygen_is_capped(self):
        s = make_sim({"player": {
            "pos": [20, 0], "oxygen_ticks": 1799
        }})
        tick(s)
        self.assertEqual(s.oxygen_ticks, s.oxygen_max)

    def test_04_oxygen_empty_event(self):
        s = make_sim({"player": {
            "pos": [20, 5], "oxygen_ticks": 1
        }})
        events = tick(s)
        self.assertEqual(s.oxygen_ticks, 0)
        self.assertTrue(has_event(events, "oxygen_empty"))

    def test_05_choke_reduces_hp(self):
        s = make_sim({"player": {
            "pos": [20, 5], "oxygen_ticks": 0,
            "hp": 3, "zero_oxy_ticks": 59
        }})
        events = tick(s)
        self.assertEqual(s.hp, 2)
        self.assertTrue(has_event(events, "choke"))

    def test_06_faint_clears_inventory(self):
        s = make_sim({
            "player": {
                "pos": [20, 5], "oxygen_ticks": 0,
                "hp": 1, "zero_oxy_ticks": 59
            },
            "hold": ["ca_linh", "bong_sung"]
        })
        events = tick(s)
        self.assertTrue(s.done)
        self.assertEqual(s.reason, "fainted")
        self.assertEqual(s.hold, [])
        self.assertEqual(s.inventory_items(), [])
        self.assertTrue(has_event(events, "faint"))
        end = next(data for name, data in events
                   if name == "gather_end")
        self.assertEqual(end["inventory"], {"items": []})

    def test_07_gather_plant(self):
        s = make_sim({"player": {"pos": [12, 0]}})
        events = tick(s, buttons=("interact",))
        self.assertEqual([(i["id"], i["kind"]) for i in s.hold], [("I1", "bong_dien_dien")])
        self.assertTrue(has_event(events, "gather"))

    def test_08_plant_regrowth(self):
        s = make_sim({"player": {"pos": [12, 0]}})
        tick(s, buttons=("interact",))
        node = next(n for n in s.nodes if n["id"] == "N1")
        self.assertEqual(node["regrow_ticks"], 1200)

        tick(s, buttons=("interact",))
        self.assertEqual(len(s.hold), 1)

        events = []
        for _ in range(1199):
            events = tick(s)

        self.assertEqual(node["regrow_ticks"], 0)
        self.assertTrue(has_event(events, "node_regrown"))

    def test_09_catch_ca_linh(self):
        s = make_sim({"player": {"pos": [15, 5]}})
        events = tick(s, buttons=("catch",))
        self.assertEqual([(i["id"], i["kind"]) for i in s.hold], [("I1", "ca_linh"), ("I2", "ca_linh"), ("I3", "ca_linh")])
        self.assertTrue(has_event(events, "fish_caught"))

    def test_10_catch_cooldown(self):
        s = make_sim({"player": {"pos": [15, 5]}})
        tick(s, buttons=("catch",))
        self.assertEqual(s.catch_cd_ticks, 30)

        before = list(s.hold)
        tick(s, buttons=("catch",))
        self.assertEqual(s.hold, before)

    def test_11_hold_full_plant(self):
        s = make_sim({
            "player": {"pos": [12, 0]},
            "hold": ["ca_loc"] * 12
        })
        events = tick(s, buttons=("interact",))
        self.assertEqual(len(s.hold), 12)
        self.assertTrue(has_event(events, "hold_full"))

    def test_12_hold_full_fish(self):
        s = make_sim({
            "player": {"pos": [15, 5]},
            "hold": ["ca_loc"] * 10
        })
        events = tick(s, buttons=("catch",))
        self.assertEqual(len(s.hold), 10)
        self.assertTrue(has_event(events, "hold_full"))
        self.assertTrue(any(f["id"] == "F1" for f in s.fish))

    def test_13_dock_ends_gather(self):
        s = make_sim({
            "player": {"pos": [2, 0]},
            "hold": ["ca_linh", "bong_sung"]
        })
        events = tick(s, buttons=("interact",))
        self.assertTrue(s.done)
        self.assertEqual(s.reason, "docked")
        self.assertTrue(has_event(events, "gather_end"))

    def test_14_inventory_conversion(self):
        s = make_sim({
            "hold": [
                "ca_linh", "ca_linh",
                "bong_sung", "ca_loc"
            ]
        })
        items = s.inventory_items()
        self.assertEqual(
            {k: sum(i["kind"] == k for i in items)
             for k in ("ca_linh", "bong_sung", "ca_loc")},
            {"ca_linh": 2, "bong_sung": 1, "ca_loc": 1}
        )
        self.assertEqual(len({i["id"] for i in items}), len(items))
        self.assertTrue(all(0 <= i["fresh"] <= 100 for i in items))

    def test_15_no_catch_at_surface(self):
        s = make_sim({
            "player": {"pos": [15, 0]},
            "fish": [{
                "id": "F1", "kind": "ca_linh",
                "pos": [15, 0]
            }]
        })
        events = tick(s, buttons=("catch",))
        self.assertEqual(s.hold, [])
        self.assertFalse(has_event(events, "fish_caught"))


if __name__ == "__main__":
    unittest.main()
