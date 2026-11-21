"""Gather v1.2 (TICKET-03): cá thể fresh 100 khi hái/bắt, hao giỏ ở đầu bước, spoiled đúng một lần theo id."""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.items import ItemIds
from chonoi.runner import Session

T = copy.deepcopy(load_contract()["tuning"])
T["freshness"] = {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}
IDLE = InputState((0.0, 0.0), set(), set())
INTERACT = InputState((0.0, 0.0), {"interact"}, {"interact"})
CATCH = InputState((0.0, 0.0), {"catch"}, {"catch"})


def session(sc):
    return Session("gather", T, sc, 1)


class GatherV12(unittest.TestCase):
    def test_ticket_fixture_spoils_on_first_step(self):
        s = session({"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}], "random_fish": False, "monsters": []})
        rows = s.step(IDLE)
        self.assertEqual([(r["tick"], r["name"], r["data"]) for r in rows],
                         [(1, "spoiled", {"item_id": "I1", "kind": "ca_linh", "location": "hold"})])
        self.assertEqual(s.step(IDLE), [], "spoiled đúng một lần")
        self.assertAlmostEqual(s.snapshot()["hold"][0]["fresh"], 30 - 2 * 0.5 / 60, delta=1e-9)

    def test_harvest_creates_fresh_item_decaying_from_next_step(self):
        s = session({"player": {"pos": [20, 0]}, "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [21, 0]}],
                     "hold": [{"id": "I4", "kind": "ca_loc", "fresh": 50}], "random_fish": False, "monsters": []})
        s.step(INTERACT)
        hold = s.snapshot()["hold"]
        self.assertEqual([(h["id"], h["kind"]) for h in hold], [("I4", "ca_loc"), ("I5", "bong_sung")])
        self.assertEqual(hold[1]["fresh"], 100, "hàng mới chưa hao ở bước được hái")
        s.step(IDLE)
        self.assertAlmostEqual(s.snapshot()["hold"][1]["fresh"], 100 - 0.5 / 60, delta=1e-9)

    def test_catch_school_creates_one_item_per_yield(self):
        s = session({"player": {"pos": [20, 5]}, "nodes": [], "random_fish": False, "monsters": [],
                     "fish": [{"id": "F1", "kind": "ca_linh", "pos": [21, 5]}]})
        s.step(CATCH)
        hold = s.snapshot()["hold"]
        self.assertEqual([h["id"] for h in hold], ["I1", "I2", "I3"])
        self.assertTrue(all(h["kind"] == "ca_linh" and h["fresh"] == 100 for h in hold))

    def test_shared_item_ids_continue(self):
        ids = ItemIds()
        ids.reserve("I41")
        from chonoi.ids import IdAllocator
        from chonoi.rng import Streams
        from chonoi.sim.gather import GatherSim
        sim = GatherSim(T, {"player": {"pos": [20, 0]}, "random_fish": False, "monsters": [],
                            "nodes": [{"id": "N1", "kind": "keo_neo", "pos": [21, 0]}]},
                        Streams(1), IdAllocator(), item_ids=ids)
        sim.step(INTERACT)
        self.assertEqual([h["id"] for h in sim.hold], ["I42"])

    def test_gather_end_inventory_is_item_list_sorted_by_id(self):
        s = session({"hold": [{"id": "I10", "kind": "ca_loc", "fresh": 100}, {"id": "I2", "kind": "ca_linh", "fresh": 80}],
                     "random_fish": False, "monsters": []})
        end = [r for r in s.step(INTERACT) if r["name"] == "gather_end"][0]["data"]
        self.assertEqual(end["reason"], "docked")
        self.assertEqual([it["id"] for it in end["inventory"]["items"]], ["I2", "I10"])
        self.assertEqual(set(end["inventory"]["items"][0]), {"id", "kind", "fresh"})


if __name__ == "__main__":
    unittest.main()
