import json
from pathlib import Path
import unittest

from helpers import ROOT, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class GatherOxygen(unittest.TestCase):
    def setUp(self):
        tuning = json.loads(
            (Path(ROOT) / "game.contract.json").read_text(encoding="utf-8")
        )["tuning"]
        self.g = tuning["gather"]
        self.interval = self.g["choke_interval_ticks"]

    def run_gather(self, w, scenario, ticks, *input_frames, inventory_out=None):
        scenario_path = write_json(w.path("scenario.json"), {"gather": scenario})
        inputs_path = write_json(w.path("inputs.json"), frames(*input_frames))
        output_path = w.path("gather.jsonl")
        args = [
            "--mode", "gather", "--seed", "1", "--ticks", str(ticks),
            "--scenario", scenario_path, "--inputs", inputs_path,
            "--snapshot-every", "1", "--out", output_path,
        ]
        if inventory_out is not None:
            args.extend(["--inventory-out", inventory_out])
        code, stderr = run_headless(*args)
        self.assertEqual(code, 0, stderr)
        return read_jsonl(output_path)

    def test_dive_from_surface_boundary_counts_first_empty_tick(self):
        # Đúng ngưỡng vẫn là mặt nước. Frame 0 đi xuống, event mang tick 1.
        with Workdir() as w:
            rows = self.run_gather(w, {"player": {
                "pos": [20, self.g["surface_depth"]], "oxygen_ticks": 1,
            }}, 2 * self.interval, {"tick": 0, "move": [0, 1]})

        by_tick = {row["tick"]: row for row in snapshots(rows)}
        self.assertTrue(by_tick[0]["player"]["at_surface"])
        self.assertFalse(by_tick[1]["player"]["at_surface"])
        self.assertEqual(by_tick[1]["player"]["zero_oxy_ticks"], 1)
        self.assertEqual(
            [(e["tick"], e["name"]) for e in events(rows)],
            [(1, "dive"), (1, "oxygen_empty"), (self.interval, "choke"),
             (2 * self.interval, "choke")],
        )
        self.assertEqual(
            events(rows, "dive")[0]["data"], {"pos": by_tick[1]["player"]["pos"]}
        )
        self.assertEqual(events(rows, "oxygen_empty")[0]["data"], {"oxygen_ticks": 0})

    def test_surface_on_choke_tick_refills_and_clears_counter(self):
        # Còn 1 Máu và chỉ một tick nữa sẽ ngạt nếu vẫn ở dưới nước.
        with Workdir() as w:
            rows = self.run_gather(w, {"player": {
                "pos": [20, self.g["surface_depth"] + 0.001],
                "oxygen_ticks": 0, "zero_oxy_ticks": self.interval - 1, "hp": 1,
            }}, 1, {"tick": 0, "move": [0, -1]})

        player = snapshots(rows)[-1]["player"]
        self.assertEqual(
            [(e["name"], e["data"]) for e in events(rows)],
            [("surface", {"pos": player["pos"]})],
        )
        self.assertEqual(player["oxygen_ticks"], self.g["oxygen_refill_per_tick"])
        self.assertEqual(player["zero_oxy_ticks"], 0)
        self.assertEqual(player["hp"], 1)

    def test_faint_precedes_docking_and_timeout_and_empties_inventory(self):
        # Ở dưới nước nhưng trong bán kính bến của preset, đồng thời hết giờ.
        hold = ["ca_loc", "bong_sung", "ca_linh"]
        with Workdir() as w:
            inventory = write_json(w.path("inventory.json"), {"items": {"ca_loc": 1}})
            rows = self.run_gather(w, {
                "player": {
                    "pos": [2, 1], "oxygen_ticks": 0,
                    "zero_oxy_ticks": self.interval - 1, "hp": 1,
                },
                "hold": hold,
                "time_left_ticks": 1,
            }, 3, {"tick": 0, "interact": True}, inventory_out=inventory)
            saved = json.loads(Path(inventory).read_text(encoding="utf-8"))

        self.assertEqual(snapshots(rows)[0]["hold"], hold)
        self.assertEqual(
            [(e["tick"], e["name"], e["data"]) for e in events(rows)],
            [(1, "choke", {"hp": 0}),
             (1, "faint", {"cause": "choke", "lost": hold[::-1], "hp": 0}),
             (1, "gather_end", {"reason": "fainted", "inventory": {"items": {}}})],
        )
        final = snapshots(rows)[-1]
        self.assertEqual(
            (final["hold"], final["hold_count"], final["player"]["hp"]), ([], 0, 0)
        )
        self.assertEqual((rows[-1]["reason"], rows[-1]["ticks"]), ("fainted", 1))
        self.assertEqual(saved, {"items": {}})

    def test_invulnerability_is_not_a_v10_fixture_field(self):
        # Validate trước khi runner mở đầu ra, kể cả khi chỉ dựng tick 0.
        with Workdir() as w:
            output = Path(w.path("gather.jsonl"))
            scenario = write_json(
                w.path("scenario.json"), {"gather": {"player": {"invuln_ticks": 0}}}
            )
            code, _ = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "0",
                "--scenario", scenario, "--out", str(output),
            )
            self.assertEqual(code, 2)
            self.assertFalse(output.exists())
