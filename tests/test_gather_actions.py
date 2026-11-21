import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim


def build_sim(**scenario):
    return GatherSim(load_contract()["tuning"], scenario, Streams(1), IdAllocator())


def pressed(button):
    return InputState((0.0, 0.0), {button: True}, {button})


def item(ident, kind, fresh=100):
    return {"id": ident, "kind": kind, "fresh": fresh}


class GatherActions(unittest.TestCase):
    def test_gather_at_surface_inclusive_radius_and_id_tie_break(self):
        sim = build_sim(
            player={"pos": [20, 0]},
            nodes=[
                {"id": "N10", "kind": "bong_sung", "pos": [22, 0]},
                {"id": "N2", "kind": "bong_dien_dien", "pos": [18, 0]},
            ],
        )

        events = sim.step(pressed("interact"))

        self.assertEqual(events[0][0], "gather")
        self.assertEqual(events[0][1]["node_id"], "N2")
        self.assertEqual(sim.hold, [item("I1", "bong_dien_dien")])
        self.assertEqual(sim.nodes[1]["regrow_ticks"], 20 * 60)

    def test_gather_requires_surface_and_available_node(self):
        sim = build_sim(
            player={"pos": [20, 0.6]},
            nodes=[{"id": "N1", "kind": "bong_sung", "pos": [20, 0.6], "regrow_ticks": 3}],
        )
        self.assertEqual(sim.step(pressed("interact")), [])
        self.assertEqual(sim.hold, [])

        sim.pos[1] = 0
        self.assertEqual(sim.nodes[0]["regrow_ticks"], 2)
        self.assertEqual(sim.step(pressed("interact")), [])

    def test_gather_does_not_take_partial_yield_when_full(self):
        tuning = load_contract()["tuning"]
        tuning["gather"]["hold_capacity"] = 1
        sim = GatherSim(
            tuning,
            {
                "player": {"pos": [20, 0]},
                "hold": [item("I1", "ca_loc")],
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}],
            },
            Streams(1),
            IdAllocator(),
        )

        events = sim.step(pressed("interact"))

        self.assertEqual(events, [("hold_full", {"source": "node", "source_id": "N1"})])
        self.assertEqual(
            sim.hold,
            [item("I1", "ca_loc", sim.initial_fresh - sim.decay_per_tick)],
        )
        self.assertEqual(sim.nodes[0]["regrow_ticks"], 0)

    def test_catch_at_inclusive_radius_yields_and_applies_cooldown(self):
        sim = build_sim(
            player={"pos": [20, 10]},
            fish=[
                {"id": "F1", "kind": "ca_linh", "pos": [20, 12]},
                {"id": "F2", "kind": "ca_linh", "pos": [20.8, 11.9], "heading_deg": 180},
            ],
        )

        events = sim.step(pressed("catch"))

        self.assertEqual(events[0][0], "fish_caught")
        self.assertEqual(events[0][1]["fish_id"], "F1")
        self.assertEqual(events[0][1]["yield"], 3)
        self.assertEqual(sim.hold, [item(f"I{i}", "ca_linh") for i in range(1, 4)])
        self.assertEqual(sim.catch_cd_ticks, 30)
        self.assertEqual([fish["id"] for fish in sim.fish], ["F2"])

        for _ in range(29):
            sim.step(InputState((0.0, 0.0), {}, set()))
        self.assertEqual(sim.catch_cd_ticks, 1)
        next_events = sim.step(pressed("catch"))
        self.assertEqual(next_events[0][0], "fish_caught")
        self.assertEqual(next_events[0][1]["fish_id"], "F2")

    def test_catch_requires_underwater_and_enough_capacity(self):
        sim = build_sim(
            player={"pos": [20, 0.5]},
            fish=[{"id": "F1", "kind": "ca_linh", "pos": [20, 0.5]}],
        )
        self.assertEqual(sim.step(pressed("catch")), [])

        tuning = load_contract()["tuning"]
        tuning["gather"]["hold_capacity"] = 3
        sim = GatherSim(
            tuning,
            {
                "player": {"pos": [20, 10]},
                "hold": [item("I1", "bong_sung")],
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [20, 10]}],
            },
            Streams(1),
            IdAllocator(),
        )
        events = sim.step(pressed("catch"))
        self.assertEqual(events, [("hold_full", {"source": "fish", "source_id": "F1"})])
        self.assertEqual(
            sim.hold,
            [item("I1", "bong_sung", sim.initial_fresh - sim.decay_per_tick)],
        )
        self.assertEqual(sim.catch_cd_ticks, 0)

    def test_dock_interaction_precedes_gather_and_faint_discards_hold(self):
        sim = build_sim(
            player={"pos": [2, 0]},
            nodes=[{"id": "N1", "kind": "bong_sung", "pos": [2, 0]}],
        )
        events = sim.step(pressed("interact"))
        self.assertEqual([event[0] for event in events], ["gather_end"])
        self.assertEqual(events[0][1]["reason"], "docked")
        self.assertEqual(sim.hold, [])

        sim = build_sim(hold=[item("I1", "ca_loc"), item("I2", "bong_sung")])
        events = []
        sim._finish("fainted", events)
        self.assertEqual(events[0][1]["inventory"], {"items": []})
        self.assertEqual(sim.hold, [])


if __name__ == "__main__":
    unittest.main()
