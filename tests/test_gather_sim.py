"""Unit tests for GatherSim (Lát 1: Bơi, Oxy, Ngạt, Máu; Lát 2: Hái, Bắt cá, Bến, Kho)."""

import unittest
from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import LiveInputs
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim


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
                        "hold": ["ca_loc", "bong_sung"]})
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
        self.assertEqual(faint_data["lost"], ["bong_sung", "ca_loc"])
        self.assertEqual(faint_data["hp"], 0)
        # Check inventory is empty
        self.assertEqual(sim.inventory_items(), {})

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
        self.assertEqual(sim.hold, ["bong_dien_dien"])
        # Node N1 should now be on cooldown (regrow_ticks > 0)
        n1 = next(n for n in sim.nodes if n["id"] == "N1")
        self.assertGreater(n1["regrow_ticks"], 0)

        # If interact again immediately, cannot gather
        inp.set(interact=True)
        evs = sim.step(inp.advance())
        self.assertNotIn("gather", [e[0] for e in evs])

    def test_gather_hold_full(self):
        sim = make_sim({"player": {"pos": [12, 0]}, "hold": ["ca_loc"] * 12})
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
        self.assertEqual(sim.hold, ["ca_linh", "ca_linh", "ca_linh"])
        self.assertEqual(sim.catch_cd_ticks, 30)
        # F1 removed from fish list
        self.assertNotIn("F1", [f["id"] for f in sim.fish])

    def test_catch_hold_full_keeps_fish_and_triggers_cooldown(self):
        # Hold has 10 items (capacity 12, free 2). F1 needs 3 items -> hold_full
        sim = make_sim({"player": {"pos": [15, 5]}, "hold": ["ca_loc"] * 10, "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15, 5]}]})
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


if __name__ == "__main__":
    unittest.main()
