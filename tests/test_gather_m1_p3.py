import unittest
from copy import deepcopy
from unittest.mock import patch

from chonoi.contract import load_contract
from chonoi.headless import main
from helpers import Workdir, events, frames, read_jsonl, snapshots, write_json


class GatherFreshnessPhase3(unittest.TestCase):
    def setUp(self):
        self.contract = deepcopy(load_contract())
        self.contract["contract_version"] = "1.2"
        self.tuning = self.contract["tuning"]
        self.gather = self.tuning["gather"]
        self.freshness = self.tuning["freshness"]
        self.threshold = self.freshness["spoiled_below"]
        self.decay = self.freshness["gather_decay_per_s"] / self.tuning["tick_hz"]

    @staticmethod
    def item(ident, fresh, kind="ca_linh"):
        return {"id": ident, "kind": kind, "fresh": fresh}

    def simulate(self, ticks, gather, *inputs):
        scenario = {"gather": {"random_fish": False, "monsters": [], **gather}}
        with Workdir() as workdir:
            scenario_path = write_json(workdir.path("scenario.json"), scenario)
            out = workdir.path("gather.jsonl")
            args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--snapshot-every", "1",
                    "--scenario", scenario_path, "--out", out]
            if inputs:
                input_path = write_json(workdir.path("inputs.json"), frames(*inputs))
                args.extend(["--inputs", input_path])
            # M6.4 bật v1.2 trên main sau khi tất cả module đã tích hợp.
            with patch("chonoi.headless.load_contract", return_value=self.contract):
                self.assertEqual(main(args), 0)
            return read_jsonl(out)

    def assert_items(self, actual, originals, *, active_ticks):
        self.assertEqual([(item["id"], item["kind"]) for item in actual],
                         [(item["id"], item["kind"]) for item in originals])
        for item, original in zip(actual, originals):
            expected = max(0, original["fresh"] - active_ticks * self.decay)
            if not active_ticks or expected == 0:
                self.assertEqual(item["fresh"], expected)
            else:
                self.assertLess(item["fresh"], original["fresh"])
                self.assertAlmostEqual(item["fresh"], expected, delta=0.01)

    def test_spoilage_crossing_fires_once_in_id_order_without_reordering_hold(self):
        hold = [self.item("I10", self.threshold), self.item("I2", self.threshold),
                self.item("I3", self.threshold - 0.01), self.item("I4", 0)]
        rows = self.simulate(2, {"hold": hold})
        self.assertEqual(
            [(event["tick"], event["data"]) for event in events(rows, "spoiled")],
            [(1, {"item_id": ident, "kind": "ca_linh", "location": "hold"}) for ident in ("I2", "I10")],
        )
        final = snapshots(rows)[-1]
        self.assertEqual(final["hold_count"], len(hold))
        self.assert_items(final["hold"], hold, active_ticks=2)

    def test_pause_freezes_freshness_until_resume(self):
        hold = [self.item("I1", self.threshold)]
        rows = self.simulate(4, {"hold": hold}, {"tick": 0, "pause": True}, {"tick": 1, "pause": False},
                             {"tick": 2, "pause": True})
        self.assertEqual([(event["tick"], event["name"]) for event in events(rows)],
                         [(1, "paused"), (3, "resumed"), (3, "spoiled")])
        for snapshot, active_ticks in zip(snapshots(rows), (0, 0, 0, 1, 2), strict=True):
            self.assert_items(snapshot["hold"], hold, active_ticks=active_ticks)

    def test_harvested_item_first_decays_on_the_following_tick(self):
        node = self.gather["nodes"][0]
        rows = self.simulate(2, {"player": {"pos": node["pos"]}}, {"tick": 0, "interact": True})
        self.assertEqual([event["tick"] for event in events(rows, "gather")], [1])
        _, acquired, aged = snapshots(rows)
        self.assertEqual(len(acquired["hold"]), 1)
        item = acquired["hold"][0]
        self.assertIsInstance(item, dict)
        initial = self.item(item["id"], self.freshness["initial"], node["kind"])
        self.assert_items(acquired["hold"], [initial], active_ticks=0)
        self.assert_items(aged["hold"], [initial], active_ticks=1)

    def test_monster_hit_and_lethal_faint_drop_aged_items_in_lifo_order(self):
        spawn = self.gather["monsters"]["spawns"][0]
        monster = {key: spawn[key] for key in ("id", "kind", "pos", "waypoints")}
        hold = [self.item(ident, self.freshness["initial"]) for ident in ("I2", "I10", "I1", "I3")]
        for hp in (2, 1):
            with self.subTest(hp=hp):
                rows = self.simulate(1, {"player": {"pos": spawn["pos"], "hp": hp},
                                         "hold": hold, "monsters": [monster]})
                hit = events(rows, "monster_hit")[0]
                self.assertEqual(hit["tick"], 1)
                self.assert_items(hit["data"]["lost"], [hold[3], hold[2]], active_ticks=1)
                if hp == 2:
                    self.assert_items(snapshots(rows)[-1]["hold"], hold[:2], active_ticks=1)
                    self.assertEqual(events(rows, "faint"), [])
                else:
                    self.assert_faint(rows, "monster", [hold[1], hold[0]],
                                      ["monster_hit", "faint", "gather_end"])

    def test_spoilage_precedes_choke_and_faint(self):
        hold = [self.item(ident, self.threshold) for ident in ("I2", "I10")]
        pos = self.gather["monsters"]["spawns"][0]["pos"]
        rows = self.simulate(1, {"player": {"pos": pos, "oxygen_ticks": 0, "hp": 1,
                                            "zero_oxy_ticks": self.gather["choke_interval_ticks"] - 1},
                                 "hold": hold})
        self.assert_faint(rows, "choke", list(reversed(hold)),
                          ["spoiled", "spoiled", "choke", "faint", "gather_end"])

    def assert_faint(self, rows, cause, lost, names):
        event_rows = events(rows)
        self.assertEqual([(event["tick"], event["name"]) for event in event_rows], [(1, name) for name in names])
        self.assertEqual(event_rows[-2]["data"]["cause"], cause)
        self.assert_items(event_rows[-2]["data"]["lost"], lost, active_ticks=1)
        self.assertEqual(event_rows[-1]["data"], {"reason": "fainted", "inventory": {"items": []}})
        self.assertEqual(snapshots(rows)[-1]["hold"], [])
