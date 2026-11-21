"""P3-03: giỏ cá thể ở v1.2, giữ nguyên hành vi v1.1."""

import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.freshness import Freshness
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim


T = load_contract()["tuning"]
G = T["gather"]
F = Freshness(T)


def item(n, kind="ca_linh", fresh=None):
    return {"id": f"I{n}", "kind": kind, "fresh": F.to_points(F.max_units) if fresh is None else fresh}


def gather(scenario, version="1.2", item_ids=None):
    return GatherSim(T, {"random_fish": False, "monsters": [], **scenario}, Streams(1), IdAllocator(),
                     contract_version=version, item_ids=item_ids)


def run_steps(sim, count=1, *frames):
    player = InputPlayer(frames)
    out = []
    for tick in range(count):
        if sim.done:
            break
        out.extend((tick + 1, name, data) for name, data in sim.step(player.advance(tick)))
    return out


class GatherFreshnessTests(unittest.TestCase):
    def test_spoiled_is_only_emitted_on_crossing_and_keeps_hold_full(self):
        above = F.to_points(F.spoil_units + F.decay("gather"))
        sim = gather({"hold": [item(4, fresh=above), item(2, fresh=above), item(11, fresh=0)]})
        initial = sim.snapshot()["hold"]
        result = run_steps(sim, 3)
        just_below = F.to_points(F.spoil_units - F.decay("gather"))
        self.assertEqual(result, [(2, "spoiled", item(2, fresh=just_below)),
                                  (2, "spoiled", item(4, fresh=just_below))])
        self.assertEqual(sim.snapshot()["hold_count"], 3)
        self.assertEqual([it["id"] for it in sim.inventory_items()], ["I4", "I2", "I11"])
        self.assertEqual(sim.inventory_items()[-1]["fresh"], 0)
        self.assertEqual(initial[0]["fresh"], above)

    def test_last_tick_harvest_has_full_freshness_and_keeps_existing_id(self):
        sim = gather({"player": {"pos": [20, 0]}, "nodes": [
            {"id": "N1", "kind": "bong_sung", "pos": [20, 0]},
        ], "hold": [item(7)], "time_left_ticks": 1})
        events = run_steps(sim, 1, {"tick": 0, "interact": True})
        stock = [item(7, fresh=F.to_points(F.max_units - F.decay("gather"))), item(8, kind="bong_sung")]
        self.assertEqual(events[-1], (1, "gather_end", {"reason": "time", "inventory": {"items": stock}}))
        self.assertEqual(sim.snapshot()["hold"], stock)

    def test_catch_uses_allocator_and_does_not_reuse_dropped_ids(self):
        ids = IdAllocator()
        sim = gather({"player": {"pos": [20, 5]}, "fish": [
            {"id": "F1", "kind": "ca_linh", "pos": [20, 5]},
        ], "hold": [item(8)]}, item_ids=ids)
        sim.drop_hold(1)
        run_steps(sim, 1, {"tick": 0, "catch": True})
        expected = [item(9 + n) for n in range(G["fish_yield"]["ca_linh"])]
        self.assertEqual(sim.inventory_items(), expected)
        self.assertEqual(ids.new("I"), f"I{9 + len(expected)}")

    def test_spoiled_items_still_block_pickup(self):
        hold = [item(i + 1, fresh=0) for i in range(G["hold_capacity"])]
        sim = gather({"player": {"pos": [20, 0]}, "nodes": [
            {"id": "N1", "kind": "bong_sung", "pos": [20, 0]},
        ], "hold": hold})
        self.assertEqual(run_steps(sim, 1, {"tick": 0, "interact": True}), [
            (1, "hold_full", {"action": "gather", "node_id": "N1", "required": G["node_yield"], "free": 0}),
        ])
        self.assertEqual(sim.snapshot()["hold"], hold)

    def test_monster_and_faint_emit_individuals_in_lifo_order(self):
        monster = G["monsters"]["spawns"][0]
        scenario = {"player": {"pos": monster["pos"], "hp": 1},
                    "monsters": [monster], "hold": [item(i) for i in range(1, 5)]}
        sim = gather(scenario)
        result = run_steps(sim)
        aged = F.to_points(F.max_units - F.decay("gather"))
        self.assertEqual([name for _, name, _ in result], ["monster_hit", "faint", "gather_end"])
        self.assertEqual(result[0][2]["lost"], [item(4, fresh=aged), item(3, fresh=aged)])
        self.assertEqual(result[1][2]["lost"], [item(2, fresh=aged), item(1, fresh=aged)])
        self.assertEqual(result[2][2]["inventory"], {"items": []})

    def test_choke_serializes_lost_without_touching_legacy_schema(self):
        player = {"pos": [20, 5], "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": G["choke_interval_ticks"] - 1}
        for version, hold in (("1.1", ["ca_linh", "ca_loc"]), ("1.2", [item(1), item(2, "ca_loc")])):
            with self.subTest(version=version):
                sim = gather({"player": player, "hold": hold}, version)
                result = run_steps(sim)
                lost = result[1][2]["lost"]
                self.assertEqual(lost if version == "1.1" else [it["id"] for it in lost],
                                 ["ca_loc", "ca_linh"] if version == "1.1" else ["I2", "I1"])
                self.assertEqual(sim.inventory_items(), {} if version == "1.1" else [])
        with self.assertRaises(BadInput):
            gather({"hold": ["ca_linh"]})
