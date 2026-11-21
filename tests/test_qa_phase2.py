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