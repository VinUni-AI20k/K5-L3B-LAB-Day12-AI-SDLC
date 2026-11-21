"""QA hộp đen cho AC-02, AC-03, AC-05 và AC-06 của Phase 1."""

import unittest

from helpers import events, frames, read_jsonl, run_headless, snapshots, write_json, Workdir


class GatherContract(unittest.TestCase):
    def test_ac_p1_02_oxygen_empty_event(self):
        with Workdir() as w:
            scenario = write_json(w.path("scenario.json"), {
                "gather": {
                    "player": {"pos": [50, 10], "oxygen_ticks": 1, "hp": 3, "zero_oxy_ticks": 0},
                    "time_left_ticks": 80,
                }
            })
            inputs = write_json(w.path("inputs.json"), frames({"tick": 0, "move": [0, 0]}))
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "2",
                "--scenario", scenario, "--inputs", inputs,
                "--out", w.path("gather.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("gather.jsonl"))
            oxygen = events(rows, "oxygen_empty")
            self.assertEqual(len(oxygen), 1)
            self.assertEqual(oxygen[0]["data"], {"oxygen_ticks": 0})

    def test_ac_p1_02_choke_event(self):
        with Workdir() as w:
            scenario = write_json(w.path("scenario.json"), {
                "gather": {
                    "player": {"pos": [50, 10], "oxygen_ticks": 0, "hp": 3, "zero_oxy_ticks": 58},
                    "time_left_ticks": 80,
                }
            })
            inputs = write_json(w.path("inputs.json"), frames({"tick": 0, "move": [0, 0]}))
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "2",
                "--scenario", scenario, "--inputs", inputs,
                "--out", w.path("gather.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("gather.jsonl"))
            choke = events(rows, "choke")
            self.assertEqual(len(choke), 1)
            self.assertEqual(choke[0]["data"]["hp"], 2)

    def test_ac_p1_03_gather_and_hold_full(self):
        with Workdir() as w:
            scenario = write_json(w.path("scenario.json"), {
                "gather": {
                    "player": {"pos": [44, 0]},
                    "hold": [],
                    "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [44, 0], "regrow_ticks": 0}],
                    "fish": [],
                }
            })
            inputs = write_json(w.path("inputs.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "1",
                "--scenario", scenario, "--inputs", inputs, "--out", w.path("gather.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("gather.jsonl"))
            gather = events(rows, "gather")
            self.assertEqual(len(gather), 1)
            self.assertEqual(gather[0]["data"]["kind"], "bong_sung")
            self.assertEqual(gather[0]["data"]["amount"], 1)


class QuanContract(unittest.TestCase):
    def test_ac_p1_05_customer_arrives_and_reserves_inventory(self):
        with Workdir() as w:
            scenario = write_json(w.path("scenario.json"), {
                "quan": {
                    "stock": {"bong_sung": 2},
                    "time_left_ticks": 122,
                }
            })
            code, err = run_headless(
                "--mode", "quan", "--seed", "42", "--ticks", "121",
                "--scenario", scenario, "--out", w.path("quan.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("quan.jsonl"))
            arrived = events(rows, "customer_arrived")
            self.assertTrue(arrived)
            customer = snapshots(rows)[-1]["customers"][0]
            self.assertEqual(customer["order_status"], "reserved")
            self.assertTrue(customer["reserved"])

    def test_ac_p1_06_cook_pick_serve_and_paid(self):
        with Workdir() as w:
            scenario = write_json(w.path("scenario.json"), {
                "quan": {
                    "player": {"pos": [2, 8]},
                    "stock": {"bong_sung": 2},
                    "random_customers": False,
                    "stoves": [{"id": "B1", "pos": [2, 8], "state": "idle"}],
                    "customers": [{
                        "id": "C1",
                        "table_id": "T1",
                        "dish_id": "goi_bong_sung",
                        "order_tick": 0,
                        "state": "waiting",
                        "patience_ticks_left": 3600,
                        "eat_ticks_left": 0,
                        "order_status": "reserved",
                        "reserved": {"bong_sung": 2},
                        "base_price": None,
                        "tip": None,
                    }],
                    "time_left_ticks": 1200,
                }
            })
            inputs = write_json(w.path("inputs.json"), frames(
                {"tick": 0, "interact": True},
                {"tick": 1, "interact": False},
                {"tick": 241, "interact": True},
                {"tick": 242, "interact": False, "move": [1, -0.857]},
                {"tick": 385, "move": [0, 0], "interact": True},
                {"tick": 386, "interact": False},
            ))
            code, err = run_headless(
                "--mode", "quan", "--seed", "42", "--ticks", "1300",
                "--scenario", scenario, "--inputs", inputs, "--out", w.path("quan.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("quan.jsonl"))
            self.assertTrue(events(rows, "cook_started"))
            self.assertTrue(events(rows, "dish_ready"))
            self.assertTrue(events(rows, "served"))
            self.assertTrue(events(rows, "paid"))


if __name__ == "__main__":
    unittest.main()
