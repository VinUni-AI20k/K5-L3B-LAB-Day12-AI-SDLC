import unittest

from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json


class FreshnessBoundaries(unittest.TestCase):
    def test_gather_item_at_threshold_spoils_once_on_first_tick(self):
        with Workdir() as work:
            item = {"id": "I1", "kind": "ca_linh", "fresh": 30}
            scenario = write_json(
                work.path("freshness.json"),
                {
                    "gather": {
                        "hold": [item],
                        "random_fish": False,
                        "monsters": [],
                    }
                },
            )
            output = work.path("gather.jsonl")
            code, stderr = run_headless(
                "--mode", "gather", "--seed", "42", "--ticks", "2",
                "--snapshot-every", "1", "--scenario", scenario, "--out", output,
            )
            self.assertEqual(code, 0, stderr)
            rows = read_jsonl(output)

            spoiled = events(rows, "spoiled")
            self.assertEqual([row["tick"] for row in spoiled], [1])
            self.assertEqual(
                spoiled[0]["data"],
                {"item_id": "I1", "kind": "ca_linh", "location": "hold"},
            )

            by_tick = {row["tick"]: row for row in snapshots(rows)}
            self.assertEqual(by_tick[0]["hold"], [item])
            for tick in (1, 2):
                with self.subTest(tick=tick):
                    hold = by_tick[tick]["hold"]
                    self.assertEqual(len(hold), 1)
                    self.assertEqual((hold[0]["id"], hold[0]["kind"]), ("I1", "ca_linh"))
                    self.assertAlmostEqual(
                        hold[0]["fresh"], 30 - tick * 0.5 / 60, delta=0.01,
                    )