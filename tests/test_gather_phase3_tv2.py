import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim


def item(ident, kind, fresh=100):
    return {"id": ident, "kind": kind, "fresh": fresh}


def press(button):
    return InputState((0.0, 0.0), {button: True}, {button})


class GatherFreshnessTV2(unittest.TestCase):
    def test_spoiled_item_still_occupies_capacity(self):
        tuning = load_contract()["tuning"]
        tuning["gather"]["hold_capacity"] = 1
        sim = GatherSim(
            tuning,
            {
                "player": {"pos": [12, 0]},
                "hold": [item("I1", "ca_linh", 30)],
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [12, 0]}],
                "random_fish": False,
                "monsters": [],
            },
            Streams(1),
            IdAllocator(),
        )

        events = sim.step(press("interact"))

        self.assertEqual(
            events,
            [
                ("spoiled", {"item_id": "I1", "kind": "ca_linh", "location": "hold"}),
                ("hold_full", {"source": "node", "source_id": "N1"}),
            ],
        )
        self.assertEqual(sim.hold, [item("I1", "ca_linh", 30 - sim.decay_per_tick)])
        self.assertEqual(sim.nodes[0]["regrow_ticks"], 0)

    def test_lifo_loss_preserves_item_objects_and_ids_are_not_reused(self):
        ids = IdAllocator()
        sim = GatherSim(
            load_contract()["tuning"],
            {
                "player": {"pos": [60, 23.5]},
                "hold": [
                    item("I1", "ca_loc"),
                    item("I2", "ca_linh"),
                    item("I3", "ca_keo"),
                    item("I4", "bong_sung"),
                ],
                "nodes": [{"id": "N1", "kind": "keo_neo", "pos": [12, 0]}],
                "monsters": [{
                    "id": "M10",
                    "pos": [60, 24],
                    "waypoints": [[60, 24], [61, 24]],
                }],
                "random_fish": False,
            },
            Streams(1),
            ids,
        )
        events = []

        self.assertFalse(sim._check_monster_hit(events))
        self.assertEqual(
            events[0],
            ("monster_hit", {
                "monster_id": "M10",
                "hp": 2,
                "lost": [item("I4", "bong_sung"), item("I3", "ca_keo")],
                "pos": [60.0, 23.5],
            }),
        )
        self.assertEqual(sim.hold, [item("I1", "ca_loc"), item("I2", "ca_linh")])

        sim.pos = [12, 0]
        sim._try_gather(events)

        self.assertEqual(sim.hold[-1], item("I5", "keo_neo"))

        sim.hold.clear()  # the previous phase consumed or discarded its remaining items
        next_phase = GatherSim(
            load_contract()["tuning"],
            {
                "player": {"pos": [12, 0]},
                "nodes": [{"id": "N2", "kind": "bong_sung", "pos": [12, 0]}],
                "random_fish": False,
                "monsters": [],
            },
            Streams(1),
            ids,
        )
        next_phase._try_gather([])

        self.assertEqual(next_phase.hold, [item("I6", "bong_sung")])


if __name__ == "__main__":
    unittest.main()
