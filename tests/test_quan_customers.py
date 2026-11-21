"""TV3 · Khách, giữ chỗ, no_dish, kiên nhẫn / lịch spawn."""

import unittest

from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json


class QuanCustomers(unittest.TestCase):
    def run_quan(self, workdir, scenario, ticks, seed=1, inputs=None):
        scenario_path = write_json(workdir.path("scenario.json"), {"quan": scenario})
        args = [
            "--mode", "quan", "--seed", str(seed), "--ticks", str(ticks),
            "--scenario", scenario_path, "--snapshot-every", "1",
            "--out", workdir.path("quan.jsonl"),
        ]
        if inputs is not None:
            inputs_path = write_json(workdir.path("inputs.json"), inputs)
            args.extend(["--inputs", inputs_path])
        code, stderr = run_headless(*args)
        self.assertEqual(code, 0, stderr)
        return read_jsonl(workdir.path("quan.jsonl"))

    def test_fixture_fills_reserved_from_recipe(self):
        with Workdir() as workdir:
            rows = self.run_quan(workdir, {
                "stock": {"ca_loc": 2, "bong_sung": 2},
                "random_customers": False,
                "customers": [{
                    "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                }],
                "time_left_ticks": 5,
            }, ticks=0)
        snap = snapshots(rows)[0]
        self.assertEqual(len(snap["customers"]), 1)
        c = snap["customers"][0]
        self.assertEqual(c["reserved"], {"ca_loc": 1})
        self.assertEqual(c["state"], "waiting")
        self.assertEqual(c["order_status"], "reserved")
        self.assertEqual(c["patience_ticks_left"], 3600)

    def test_busy_table_skips_spawn_without_event(self):
        """Bàn bận ở tick spawn → bỏ lượt, không customer_arrived / no_dish."""
        with Workdir() as workdir:
            rows = self.run_quan(workdir, {
                "stock": {"ca_loc": 5, "bong_sung": 5, "ca_linh": 5, "bong_dien_dien": 5},
                "customers": [{
                    "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                    "patience_ticks_left": 9999,
                }],
                "time_left_ticks": 200,
            }, ticks=120)
        self.assertEqual(events(rows, "customer_arrived"), [])
        self.assertEqual(events(rows, "no_dish"), [])
        self.assertEqual(len(snapshots(rows)[-1]["customers"]), 1)

    def test_no_dish_when_stock_insufficient(self):
        with Workdir() as workdir:
            rows = self.run_quan(workdir, {
                "stock": {},
                "random_customers": True,
                "time_left_ticks": 200,
            }, ticks=120)
        self.assertEqual(len(events(rows, "no_dish")), 1)
        self.assertEqual(events(rows, "no_dish")[0]["tick"], 120)
        self.assertEqual(events(rows, "customer_arrived"), [])

    def test_spawn_reserves_and_patience_starts_next_step(self):
        with Workdir() as workdir:
            rows = self.run_quan(workdir, {
                "stock": {"ca_loc": 2, "bong_sung": 4, "ca_linh": 6, "bong_dien_dien": 2},
                "time_left_ticks": 200,
            }, ticks=121, seed=42)
        arrived = events(rows, "customer_arrived")
        self.assertEqual(len(arrived), 1)
        self.assertEqual(arrived[0]["tick"], 120)
        data = arrived[0]["data"]
        self.assertEqual(data["table_id"], "T1")
        self.assertIn(data["dish_id"], {
            "ca_loc_nuong_trui", "goi_bong_sung", "lau_ca_linh_dien_dien",
        })

        snap_at_spawn = next(s for s in snapshots(rows) if s["tick"] == 120)
        self.assertEqual(len(snap_at_spawn["customers"]), 1)
        self.assertEqual(snap_at_spawn["customers"][0]["patience_ticks_left"], 3600)
        recipe = {
            "ca_loc_nuong_trui": {"ca_loc": 1},
            "goi_bong_sung": {"bong_sung": 2},
            "lau_ca_linh_dien_dien": {"bong_dien_dien": 1, "ca_linh": 3},
        }[data["dish_id"]]
        self.assertEqual(snap_at_spawn["customers"][0]["reserved"], recipe)

        snap_next = next(s for s in snapshots(rows) if s["tick"] == 121)
        self.assertEqual(snap_next["customers"][0]["patience_ticks_left"], 3599)

    def test_patience_leave_releases_reserved_and_clears_stove(self):
        with Workdir() as workdir:
            rows = self.run_quan(workdir, {
                "stock": {"ca_loc": 0},
                "random_customers": False,
                "customers": [{
                    "id": "C9", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                    "order_status": "assigned", "patience_ticks_left": 1,
                    "reserved": {},
                }],
                "stoves": [{
                    "id": "B1", "state": "cooking",
                    "dish": {"order_id": "C9", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                    "cook_ticks_left": 100,
                }],
                "time_left_ticks": 10,
            }, ticks=1)
        left = events(rows, "customer_left")
        self.assertEqual(len(left), 1)
        self.assertEqual(left[0]["data"]["reason"], "patience")
        self.assertEqual(left[0]["data"]["order_id"], "C9")
        self.assertAlmostEqual(left[0]["data"]["reputation"], 2.5)

        snap = snapshots(rows)[-1]
        self.assertEqual(snap["customers"], [])
        self.assertEqual(snap["stoves"][0]["state"], "idle")
        self.assertIsNone(snap["stoves"][0]["dish"])
        self.assertAlmostEqual(snap["reputation"], 2.5)

    def test_closing_leaves_waiting_without_reputation_hit(self):
        with Workdir() as workdir:
            rows = self.run_quan(workdir, {
                "stock": {"ca_loc": 1},
                "random_customers": False,
                "customers": [{
                    "id": "C2", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                    "patience_ticks_left": 500,
                }],
                "time_left_ticks": 1,
            }, ticks=2)
        left = events(rows, "customer_left")
        self.assertEqual(len(left), 1)
        self.assertEqual(left[0]["data"]["reason"], "closing")
        self.assertAlmostEqual(left[0]["data"]["reputation"], 3.0)
        self.assertEqual(events(rows, "quan_end")[0]["data"]["reason"], "time")
        self.assertAlmostEqual(snapshots(rows)[-1]["reputation"], 3.0)
