"""Unit tests for GatherSim (Lát 1: Bơi, Oxy, Ngạt, Máu; Lát 2: Hái, Bắt cá, Bến, Kho)."""

import unittest
from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import LiveInputs
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim


# P3 [THAY THẾ]: fixture giỏ là cá thể có id và fresh, theo thứ tự nhặt.
def items(kinds, fresh=100, start=1):
    return [{"id": f"I{i}", "kind": kind, "fresh": fresh}
            for i, kind in enumerate(kinds, start)]


# P3 [THAY THẾ]: bộ nhớ sim dùng fresh_u nguyên, đầu ra dùng fresh.
def internal_items(kinds, fresh_u=24000, start=1):
    return [{"id": f"I{i}", "kind": kind, "fresh_u": fresh_u}
            for i, kind in enumerate(kinds, start)]


def make_sim(scenario=None):
    contract = load_contract()
    tuning = contract["tuning"]
    sc = scenario or {}
    streams = Streams(42)
    ids = IdAllocator()
    return GatherSim(tuning, sc, streams, ids)


class TestGatherSim(unittest.TestCase):
    def test_dive_and_surface_events(self):
        # Start at surface [2, 0]
        sim = make_sim({"player": {"pos": [2, 0]}})
        inp = LiveInputs()
        # Move down [0, 1] to dive past 0.5
        inp.set(move=[0, 1])
        all_events = []
        for _ in range(30):
            evs = sim.step(inp.advance())
            all_events.extend(evs)
        dive_evs = [e for e in all_events if e[0] == "dive"]
        self.assertTrue(len(dive_evs) >= 1)
        self.assertIn("pos", dive_evs[0][1])

        # Move up [0, -1] to surface
        inp.set(move=[0, -1])
        for _ in range(60):
            evs = sim.step(inp.advance())
            all_events.extend(evs)
        surface_evs = [e for e in all_events if e[0] == "surface"]
        self.assertTrue(len(surface_evs) >= 1)

    def test_oxygen_depletion_and_choke_and_faint(self):
        # Start underwater with oxygen_ticks = 1, hp = 1
        sim = make_sim({"player": {"pos": [20, 5], "oxygen_ticks": 1, "hp": 1, "zero_oxy_ticks": 0},
                        "hold": items(["ca_loc", "bong_sung"])})
        inp = LiveInputs()
        # Tick 1: drops from 1 to 0 -> oxygen_empty
        evs = sim.step(inp.advance())
        ev_names = [e[0] for e in evs]
        self.assertIn("oxygen_empty", ev_names)
        self.assertEqual(sim.zero_oxy_ticks, 1)

        # Step 58 more ticks (total 59 ticks with oxy 0): zero_oxy_ticks reaches 59
        for _ in range(58):
            evs = sim.step(inp.advance())
            self.assertFalse(sim.done)

        # 60th tick underwater with oxy 0: triggers choke, and since hp=1 -> hp becomes 0 -> faint -> gather_end
        evs = sim.step(inp.advance())
        names = [e[0] for e in evs]
        self.assertIn("choke", names)
        self.assertIn("faint", names)
        self.assertIn("gather_end", names)
        self.assertTrue(sim.done)
        self.assertEqual(sim.reason, "fainted")
        # Check faint payload: cause "choke", lost reversed hold LIFO
        faint_data = next(e[1] for e in evs if e[0] == "faint")
        # P3 [THAY THẾ]: cá thể có id và độ tươi, lost vẫn theo LIFO.
        self.assertEqual(faint_data["lost"], list(reversed(items(["ca_loc", "bong_sung"], 99.5))))
        self.assertEqual(faint_data["hp"], 0)
        # Check inventory is empty
        # P3 [THAY THẾ]: cá thể có id và độ tươi, lost vẫn theo LIFO.
        self.assertEqual(sim.inventory_items(), [])

    def test_surface_prevents_choke(self):
        # Start underwater at d=0.51 with initial vel moving up, oxygen=0, zero_oxy_ticks = 59
        sim = make_sim({"player": {"pos": [20, 0.51], "vel": [0, -2.0], "oxygen_ticks": 0, "hp": 3, "zero_oxy_ticks": 59}})
        inp = LiveInputs()
        # Move up to surface
        inp.set(move=[0, -1])
        evs = sim.step(inp.advance())
        # Should cross 0.5 to surface, refill oxygen, zero_oxy_ticks reset to 0, no choke!
        names = [e[0] for e in evs]
        self.assertIn("surface", names)
        self.assertNotIn("choke", names)
        self.assertEqual(sim.hp, 3)
        self.assertEqual(sim.zero_oxy_ticks, 0)
        self.assertGreater(sim.oxygen_ticks, 0)

    def test_gather_node_and_regrow(self):
        # Place player at [12, 0] near node N1 (kind: bong_dien_dien)
        sim = make_sim({"player": {"pos": [12, 0]}, "hold": []})
        inp = LiveInputs()
        inp.set(interact=True)
        evs = sim.step(inp.advance())
        names = [e[0] for e in evs]
        self.assertIn("gather", names)
        gather_data = next(e[1] for e in evs if e[0] == "gather")
        self.assertEqual(gather_data["node_id"], "N1")
        self.assertEqual(gather_data["kind"], "bong_dien_dien")
        self.assertEqual(gather_data["amount"], 1)
        # P3 [THAY THẾ]: cá thể có id và độ tươi, lost vẫn theo LIFO.
        self.assertEqual(sim.hold, internal_items(["bong_dien_dien"]))
        # Node N1 should now be on cooldown (regrow_ticks > 0)
        n1 = next(n for n in sim.nodes if n["id"] == "N1")
        self.assertGreater(n1["regrow_ticks"], 0)

        # If interact again immediately, cannot gather
        inp.set(interact=True)
        evs = sim.step(inp.advance())
        self.assertNotIn("gather", [e[0] for e in evs])

    def test_gather_hold_full(self):
        sim = make_sim({"player": {"pos": [12, 0]}, "hold": items(["ca_loc"] * 12)})
        inp = LiveInputs()
        inp.set(interact=True)
        evs = sim.step(inp.advance())
        names = [e[0] for e in evs]
        self.assertIn("hold_full", names)
        hf_data = next(e[1] for e in evs if e[0] == "hold_full")
        self.assertEqual(hf_data["action"], "gather")
        self.assertEqual(hf_data["node_id"], "N1")
        self.assertEqual(hf_data["required"], 1)
        self.assertEqual(hf_data["free"], 0)

    def test_catch_fish_and_cooldown(self):
        # Fish F1 is ca_linh at [15, 5], yield = 3
        sim = make_sim({"player": {"pos": [15, 5]}, "hold": [], "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15, 5]}]})
        inp = LiveInputs()
        inp.set(catch=True)
        evs = sim.step(inp.advance())
        names = [e[0] for e in evs]
        self.assertIn("fish_caught", names)
        fc_data = next(e[1] for e in evs if e[0] == "fish_caught")
        self.assertEqual(fc_data["fish_id"], "F1")
        self.assertEqual(fc_data["kind"], "ca_linh")
        self.assertEqual(fc_data["yield"], 3)
        # P3 [THAY THẾ]: cá thể có id và độ tươi, lost vẫn theo LIFO.
        self.assertEqual(sim.hold, internal_items(["ca_linh", "ca_linh", "ca_linh"]))
        self.assertEqual(sim.catch_cd_ticks, 30)
        # F1 removed from fish list
        self.assertNotIn("F1", [f["id"] for f in sim.fish])

    def test_catch_hold_full_keeps_fish_and_triggers_cooldown(self):
        # Hold has 10 items (capacity 12, free 2). F1 needs 3 items -> hold_full
        sim = make_sim({"player": {"pos": [15, 5]}, "hold": items(["ca_loc"] * 10), "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15, 5]}]})
        inp = LiveInputs()
        inp.set(catch=True)
        evs = sim.step(inp.advance())
        names = [e[0] for e in evs]
        self.assertIn("hold_full", names)
        hf_data = next(e[1] for e in evs if e[0] == "hold_full")
        self.assertEqual(hf_data["action"], "catch")
        self.assertEqual(hf_data["fish_id"], "F1")
        self.assertEqual(hf_data["required"], 3)
        self.assertEqual(hf_data["free"], 2)
        # F1 still present! No cooldown when hold is full per clarify #5!
        self.assertIn("F1", [f["id"] for f in sim.fish])
        self.assertEqual(sim.catch_cd_ticks, 0)


class TestGatherFreshness(unittest.TestCase):
    """P3: ngưỡng nguyên, thứ tự tick, cá thể và đầu ra bàn giao."""

    def test_exact_threshold_spoils_once_on_first_step(self):
        sim = make_sim({"hold": items(["ca_linh"], 30), "random_fish": False, "monsters": []})
        inp = LiveInputs()
        evs = sim.step(inp.advance())
        self.assertEqual(evs, [("spoiled", {"item_id": "I1", "kind": "ca_linh", "location": "hold"})])
        self.assertEqual(sim.hold[0]["fresh_u"], 7198)
        self.assertEqual(sim.step(inp.advance()), [])

    def test_reaching_threshold_is_not_yet_spoiled(self):
        sim = make_sim({"hold": items(["ca_linh"], 30 + 2 / 240),
                        "random_fish": False, "monsters": []})
        inp = LiveInputs()
        self.assertEqual(sim.step(inp.advance()), [])
        self.assertEqual(sim.hold[0]["fresh_u"], 7200)
        self.assertEqual([name for name, _ in sim.step(inp.advance())], ["spoiled"])

    def test_spoiled_events_sorted_by_numeric_id_before_docking(self):
        hold = [{"id": ident, "kind": "ca_linh", "fresh": 30} for ident in ("I10", "I2", "I1")]
        sim = make_sim({"hold": hold, "random_fish": False, "monsters": []})
        inp = LiveInputs()
        inp.set(interact=True)
        evs = sim.step(inp.advance())
        self.assertEqual([name for name, _ in evs], ["spoiled"] * 3 + ["gather_end"])
        self.assertEqual([data["item_id"] for _, data in evs[:-1]], ["I1", "I2", "I10"])
        self.assertEqual([it["id"] for it in sim.snapshot()["hold"]], ["I10", "I2", "I1"])
        self.assertEqual(evs[-1][1]["inventory"]["items"],
                         sorted(sim.snapshot()["hold"], key=lambda it: int(it["id"][1:])))

    def test_decay_half_point_per_second(self):
        sim = make_sim({"hold": items(["ca_loc"]), "random_fish": False, "monsters": []})
        inp = LiveInputs()
        for _ in range(60):
            sim.step(inp.advance())
        self.assertEqual(sim.hold, internal_items(["ca_loc"], fresh_u=23880))
        self.assertEqual(sim.snapshot()["hold"], items(["ca_loc"], 99.5))

    def test_already_spoiled_clamps_at_zero_without_event(self):
        sim = make_sim({"hold": items(["ca_linh"], 1 / 240),
                        "random_fish": False, "monsters": []})
        inp = LiveInputs()
        for _ in range(3):
            self.assertEqual(sim.step(inp.advance()), [])
        self.assertEqual(sim.hold, internal_items(["ca_linh"], fresh_u=0))
        self.assertEqual(sim.snapshot()["hold_count"], 1)

    def test_new_harvest_starts_at_100_then_decays_next_step(self):
        sim = make_sim({"player": {"pos": [12, 0]}, "hold": items(["ca_loc"]),
                        "random_fish": False, "monsters": []})
        inp = LiveInputs()
        inp.set(interact=True)
        sim.step(inp.advance())
        self.assertEqual(sim.hold[0]["fresh_u"], 23998)
        self.assertEqual(sim.hold[1], {"id": "I2", "kind": "bong_dien_dien", "fresh_u": 24000})
        sim.step(inp.advance())
        self.assertEqual(sim.hold[1]["fresh_u"], 23998)

    def test_new_catch_has_distinct_ids_and_does_not_decay_same_step(self):
        sim = make_sim({"player": {"pos": [15, 5]}, "hold": items(["ca_loc"], start=10),
                        "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15, 5]}],
                        "random_fish": False, "monsters": []})
        inp = LiveInputs()
        inp.set(catch=True)
        sim.step(inp.advance())
        self.assertEqual(sim.hold, internal_items(["ca_loc"], fresh_u=23998, start=10)
                         + internal_items(["ca_linh"] * 3, start=11))

    def test_faint_lifo_uses_pick_order_not_id_and_preserves_freshness(self):
        hold = [{"id": "I10", "kind": "ca_loc", "fresh": 80},
                {"id": "I2", "kind": "ca_loc", "fresh": 30}]
        sim = make_sim({"player": {"pos": [20, 5], "hp": 1, "oxygen_ticks": 0,
                                   "zero_oxy_ticks": 59}, "hold": hold,
                        "random_fish": False, "monsters": []})
        evs = sim.step(LiveInputs().advance())
        self.assertEqual([name for name, _ in evs], ["spoiled", "choke", "faint", "gather_end"])
        self.assertEqual(evs[2][1]["lost"], [
            {"id": "I2", "kind": "ca_loc", "fresh": round(30 - 2 / 240, 6)},
            {"id": "I10", "kind": "ca_loc", "fresh": round(80 - 2 / 240, 6)}])
        self.assertEqual(evs[-1][1]["inventory"], {"items": []})

    def test_inventory_is_sorted_internal_copy_and_snapshot_is_external(self):
        hold = [{"id": "I10", "kind": "ca_loc", "fresh": 80},
                {"id": "I2", "kind": "ca_keo", "fresh": 70}]
        sim = make_sim({"hold": hold, "random_fish": False, "monsters": []})
        inventory = sim.inventory_items()
        snapshot = sim.snapshot()
        self.assertEqual(inventory, [
            {"id": "I2", "kind": "ca_keo", "fresh_u": 16800},
            {"id": "I10", "kind": "ca_loc", "fresh_u": 19200}])
        self.assertEqual(snapshot["hold"], hold)
        sim.step(LiveInputs().advance())
        self.assertEqual(snapshot["hold"], hold)
        inventory[0]["fresh_u"] = 0
        self.assertNotEqual(sim.hold[1]["fresh_u"], 0)

    def test_item_ids_continue_across_gather_instances_after_loss(self):
        tuning = load_contract()["tuning"]
        ids = IdAllocator()
        sim = GatherSim(tuning, {"player": {"pos": [20, 5], "hp": 1, "oxygen_ticks": 0,
                                            "zero_oxy_ticks": 59},
                                 "hold": items(["ca_loc"], start=10),
                                 "random_fish": False, "monsters": []}, Streams(42), ids)
        sim.step(LiveInputs().advance())
        next_sim = GatherSim(tuning, {"player": {"pos": [12, 0]},
                                      "random_fish": False, "monsters": []}, Streams(42), ids)
        inp = LiveInputs()
        inp.set(interact=True)
        next_sim.step(inp.advance())
        self.assertEqual(next_sim.hold, internal_items(["bong_dien_dien"], start=11))


if __name__ == "__main__":
    unittest.main()
