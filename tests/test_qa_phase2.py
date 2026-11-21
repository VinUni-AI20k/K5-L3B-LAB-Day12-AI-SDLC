import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class DayShopBoundaries(unittest.TestCase):
    def test_exact_price_purchase_applies_on_next_day(self):
        with Workdir() as work:
            scenario = write_json(
                work.path("scenario.json"),
                {
                    "day": {"money": 200, "earned": 200},
                    "gather": {"random_fish": False, "monsters": []},
                    "quan": {"time_left_ticks": 1, "random_customers": False},
                },
            )
            inputs = write_json(
                work.path("inputs.json"),
                frames(
                    {"tick": 0, "interact": True},
                    {"tick": 1, "interact": False},
                    {"tick": 2, "buy": "oxygen"},
                    {"tick": 3, "shop_done": True},
                ),
            )
            output = work.path("day.jsonl")
            code, stderr = run_headless(
                "--mode", "day", "--seed", "42", "--days", "2",
                "--ticks", "4", "--snapshot-every", "1",
                "--scenario", scenario, "--inputs", inputs, "--out", output,
            )
            self.assertEqual(code, 0, stderr)
            rows = read_jsonl(output)
            by_tick = {row["tick"]: row for row in snapshots(rows)}

            self.assertEqual(by_tick[1]["phase"], "quan")
            self.assertEqual(by_tick[1]["phase_tick"], 0)
            self.assertEqual(by_tick[2]["phase"], "shop")
            self.assertEqual(by_tick[2]["phase_tick"], 0)

            purchases = events(rows, "bought")
            self.assertEqual(len(purchases), 1)
            self.assertEqual(purchases[0]["tick"], 3)
            self.assertEqual(
                purchases[0]["data"],
                {"upgrade": "oxygen", "level": 1, "price": 200, "money": 0},
            )
            self.assertEqual(by_tick[3]["upgrades"]["oxygen"], 1)
            self.assertEqual(by_tick[3]["active_upgrades"].get("oxygen", 0), 0)
            self.assertEqual(by_tick[3]["earned"], 200)

            next_day = by_tick[4]
            self.assertEqual((next_day["day"], next_day["phase"]), (2, "gather"))
            self.assertEqual(next_day["phase_tick"], 0)
            self.assertEqual(next_day["active_upgrades"]["oxygen"], 1)
            self.assertEqual(next_day["player"]["oxygen_ticks"], 2700)
            self.assertEqual(rows[-1]["days_completed"], 1)

class PauseBoundaries(unittest.TestCase):
    def test_gather_pause_freezes_clock_and_resume_steps_immediately(self):
        with Workdir() as work:
            inputs = write_json(
                work.path("pause-inputs.json"),
                frames(
                    {"tick": 0, "pause": True},
                    {"tick": 1, "pause": False},
                    {"tick": 2, "pause": True},
                ),
            )
            output = work.path("pause.jsonl")
            code, stderr = run_headless(
                "--mode", "gather", "--seed", "42", "--ticks", "3",
                "--snapshot-every", "1", "--inputs", inputs, "--out", output,
            )
            self.assertEqual(code, 0, stderr)
            rows = read_jsonl(output)
            by_tick = {row["tick"]: row for row in snapshots(rows)}
            initial = by_tick[0]

            for tick in (1, 2):
                with self.subTest(tick=tick):
                    snapshot = by_tick[tick]
                    self.assertEqual(snapshot["state"], "paused")
                    for field in ("sim_tick", "phase_tick", "time_left_ticks"):
                        self.assertEqual(snapshot[field], initial[field], field)

            resumed = by_tick[3]
            self.assertEqual(resumed["state"], "playing")
            self.assertEqual(resumed["sim_tick"], initial["sim_tick"] + 1)
            self.assertEqual(resumed["phase_tick"], initial["phase_tick"] + 1)
            self.assertEqual(resumed["time_left_ticks"], initial["time_left_ticks"] - 1)
            self.assertEqual([row["tick"] for row in events(rows, "paused")], [1])
            self.assertEqual([row["tick"] for row in events(rows, "resumed")], [3])

class MonsterBoundaries(unittest.TestCase):
    def test_lethal_crocodile_hit_drops_items_in_two_stages(self):
        with Workdir() as work:
            scenario = write_json(
                work.path("monster.json"),
                {
                    "gather": {
                        "player": {"pos": [60, 24], "hp": 1},
                        "hold": ["ca_loc", "bong_sung", "bong_dien_dien"],
                        "random_fish": False,
                        "monsters": [
                            {
                                "id": "M1",
                                "kind": "ca_sau",
                                "pos": [60, 24],
                                "waypoints": [[60, 24], [64, 24]],
                            }
                        ],
                    }
                },
            )
            output = work.path("gather.jsonl")
            inventory = work.path("inventory.json")
            code, stderr = run_headless(
                "--mode", "gather", "--seed", "42", "--ticks", "1",
                "--scenario", scenario, "--out", output,
                "--inventory-out", inventory,
            )
            self.assertEqual(code, 0, stderr)
            rows = read_jsonl(output)

            terminal_events = [
                row for row in events(rows)
                if row["name"] in ("monster_hit", "faint", "gather_end")
            ]
            self.assertEqual(
                [(row["tick"], row["name"]) for row in terminal_events],
                [(1, "monster_hit"), (1, "faint"), (1, "gather_end")],
            )
            hit, faint, gather_end = (row["data"] for row in terminal_events)
            self.assertEqual(hit["monster_id"], "M1")
            self.assertEqual(hit["hp"], 0)
            lost_hit = [it["kind"] if isinstance(it, dict) else it for it in hit["lost"]]
            self.assertEqual(lost_hit, ["bong_dien_dien"])
            lost_faint = [it["kind"] if isinstance(it, dict) else it for it in faint["lost"]]
            self.assertEqual(lost_faint, ["bong_sung", "ca_loc"])
            self.assertEqual(faint["cause"], "monster")
            self.assertEqual(faint["hp"], 0)
            self.assertEqual(gather_end["reason"], "fainted")
            expected_empty = {"items": []} if isinstance(gather_end["inventory"].get("items"), list) else {"items": {}}
            self.assertEqual(gather_end["inventory"], expected_empty)

            with open(inventory, encoding="utf-8") as exported:
                self.assertEqual(json.load(exported), gather_end["inventory"])