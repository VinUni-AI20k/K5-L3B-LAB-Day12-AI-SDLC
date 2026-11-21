import unittest

from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json


class GatherPhase2(unittest.TestCase):
    def run_case(self, work, scenario, ticks):
        path = write_json(work.path("scenario.json"), {"gather": scenario})
        output = work.path("out.jsonl")
        code, err = run_headless("--mode", "gather", "--seed", "42", "--ticks", str(ticks),
                                 "--scenario", path, "--snapshot-every", "1", "--out", output)
        self.assertEqual(code, 0, err)
        return read_jsonl(output)

    def test_fish_reflects_and_scheduled_spawn_occurs(self):
        with Workdir() as work:
            rows = self.run_case(work, {"monsters": [], "fish": [{"id": "F1", "kind": "ca_linh", "pos": [96, 5], "heading_deg": 0}]}, 360)
            self.assertLess(snapshots(rows)[1]["fish"][0]["pos"][0], 96)
            spawned = events(rows, "fish_spawned")
            self.assertEqual([e["tick"] for e in spawned], [360])
            self.assertEqual(len(snapshots(rows)[-1]["fish"]), 2)

    def test_disabled_random_fish_keeps_fixture_stationary(self):
        with Workdir() as work:
            rows = self.run_case(work, {"random_fish": False, "monsters": [], "fish": [{"id": "F1", "kind": "ca_linh", "pos": [20, 5]}]}, 360)
            self.assertEqual(snapshots(rows)[-1]["fish"][0]["pos"], [20, 5])
            self.assertEqual(events(rows, "fish_spawned"), [])

    def test_monster_hit_drops_half_lifo_and_invulnerability_prevents_repeat(self):
        with Workdir() as work:
            scenario = {"player": {"pos": [60, 24]}, "random_fish": False,
                        "hold": ["ca_loc", "bong_sung", "ca_linh", "keo_neo"]}
            rows = self.run_case(work, scenario, 2)
            hits = events(rows, "monster_hit")
            self.assertEqual(len(hits), 1)
            lost_kinds = [it["kind"] if isinstance(it, dict) else it for it in hits[0]["data"]["lost"]]
            self.assertEqual(lost_kinds, ["keo_neo", "ca_linh"])
            self.assertEqual(snapshots(rows)[-1]["player"]["hp"], 2)


if __name__ == "__main__":
    unittest.main()
