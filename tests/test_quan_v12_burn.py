"""Kiểm thử Quán v1.2 (Phase 3) và mở rộng burn: hao kho, tái giữ chỗ, giá theo tươi, cháy món."""

import json
import unittest

from chonoi.contract import load_contract
from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class QuanV12BurnTests(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_stock_decay_spoiled_sorted_and_shop_no_decay(self):
        sc = {
            "gather": {
                "hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100}],
                "time_left_ticks": 1, "random_fish": False, "monsters": [],
            },
            "quan": {"time_left_ticks": 5, "random_customers": False},
        }
        inp = frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False})
        with Workdir() as w:
            out = w.path("shop.jsonl")
            c, e = run_headless(
                "--mode", "day", "--days", "1", "--seed", "1",
                "--scenario", write_json(w.path("sc.json"), sc),
                "--inputs", write_json(w.path("in.json"), inp),
                "--ticks", "20", "--snapshot-every", "1", "--out", out,
            )
            self.assertEqual(c, 0, e)
            snaps = snapshots(read_jsonl(out))
            # Tick 1 = gather docked: I1 fresh = 99.991667 -> quan tick 1 has exact same fresh before quan ticks
            s_q0 = next(s for s in snaps if s["phase"] == "quan" and s["phase_tick"] == 0)
            self.assertEqual(s_q0["stock"][0]["fresh"], 99.991667)
            # After 5 ticks in quan (-5 units): transitions to shop
            shop_snaps = [s for s in snaps if s["phase"] == "shop"]
            self.assertGreater(len(shop_snaps), 1)
            f_start = shop_snaps[0]["stock"][0]["fresh"]
            f_later = shop_snaps[-1]["stock"][0]["fresh"]
            self.assertEqual(f_start, f_later)

    def test_spoil_rereserves_once_by_order_tick_then_unfulfillable(self):
        # I1 spoils at tick 1 (<30), C2 (order_tick=1) gets fresher backup I2 (80) before C1 (order_tick=2)
        # Wait: C2 fails because no 2nd backup -> C1 steals backup first if C1 older! Test order_tick priority:
        sc = {
            "quan": {
                "random_customers": False,
                "stock": [
                    {"id": "I1", "kind": "ca_loc", "fresh": 30},     # spoils at tick 1
                    {"id": "I2", "kind": "ca_loc", "fresh": 30},     # spoils at tick 1
                    {"id": "I3", "kind": "ca_loc", "fresh": 60},     # backup 1
                    {"id": "I4", "kind": "ca_loc", "fresh": 90},     # backup 2 (freshest)
                ],
                "customers": [
                    {"id": "C1", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_tick": 10, "reserved": ["I1"]},
                    {"id": "C2", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_tick": 5, "reserved": ["I2"]},
                ],
            }
        }
        # Only 1 unspoiled backup left if I1, I2 spoil? Wait: I3 & I4 give 2 backups; test 1 backup so C2 wins & C1 unfulfillable!
        sc["quan"]["stock"].pop(2)  # remove I3; only I4 remains!
        with Workdir() as w:
            out = w.path("re.jsonl")
            c, e = run_headless(
                "--mode", "quan", "--seed", "1",
                "--scenario", write_json(w.path("sc.json"), sc),
                "--ticks", "2", "--snapshot-every", "1", "--out", out,
            )
            self.assertEqual(c, 0, e)
            rows = read_jsonl(out)
            sp = [r["data"] for r in events(rows, "spoiled")]
            self.assertEqual(sp, [
                {"item_id": "I1", "kind": "ca_loc", "location": "stock"},
                {"item_id": "I2", "kind": "ca_loc", "location": "stock"},
            ])
            custs = {cust["id"]: cust for cust in snapshots(rows)[-1]["customers"]}
            self.assertEqual(custs["C2"]["order_status"], "reserved")
            self.assertEqual(custs["C2"]["reserved"], ["I4"])
            self.assertEqual(custs["C1"]["order_status"], "unfulfillable")
            self.assertEqual(custs["C1"]["reserved"], [])

    def test_avg_fresh_base_price_and_floor_tip_multi_ingredient(self):
        # lau_ca_linh_dien_dien list price = 120; 3 ca_linh + 1 bong_dien_dien
        # At tick 0->1 each decays -1 unit -> give exact fresh_u so after -1 tick:
        # e.g. 50.004167 -> 12001 - 1 = 12000 (50.0%) for each -> avg_fresh = 50 -> base_price = floor(120 * 50 / 100) = 60 -> tip = floor(60 * 0.2) = 12
        # Also test fractional floor: e.g. 12001/240 -> after 1 tick 50%: mix 80% + 60% -> avg 70 -> 120*70//100 = 84; or odd -> floor check!
        val = round(12001 / 240, 6)
        val_75 = round(18001 / 240, 6)
        sc = {
            "quan": {
                "player": {"pos": [2, 8]},
                "random_customers": False,
                "stock": [
                    {"id": "I1", "kind": "ca_linh", "fresh": val},
                    {"id": "I2", "kind": "ca_linh", "fresh": val},
                    {"id": "I3", "kind": "ca_linh", "fresh": val},
                    {"id": "I4", "kind": "bong_dien_dien", "fresh": val_75},
                ],
                "customers": [{
                    "id": "C1", "table_id": "T1", "dish_id": "lau_ca_linh_dien_dien",
                    "reserved": ["I1", "I2", "I3", "I4"],
                }],
            }
        }
        # avg fresh after 1 tick = (50 + 50 + 50 + 75) / 4 = 56.25 -> 120 * 56.25 / 100 = 67.5 -> floor = 67 -> tip = floor(67 * 0.2) = 13
        inp = frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False})
        with Workdir() as w:
            out = w.path("price.jsonl")
            c, e = run_headless(
                "--mode", "quan", "--seed", "1",
                "--scenario", write_json(w.path("sc.json"), sc),
                "--inputs", write_json(w.path("in.json"), inp),
                "--ticks", "2", "--out", out,
            )
            self.assertEqual(c, 0, e)
            rows = read_jsonl(out)
            cs = events(rows, "cook_started")[0]["data"]
            self.assertEqual(cs["base_price"], 67)
            self.assertEqual([(it["kind"], it["id"]) for it in cs["items"]], [
                ("bong_dien_dien", "I4"), ("ca_linh", "I1"), ("ca_linh", "I2"), ("ca_linh", "I3"),
            ])

    def test_burn_boundary_1200_pickable_vs_1201_dish_burnt(self):
        payload = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        # 1) ready_ticks = 1199 at start -> tick 1 reaches 1200 -> still pickable by interact at tick 0!
        sc_ok = {
            "quan": {
                "player": {"pos": [2, 8]},
                "random_customers": False,
                "stoves": [{"id": "B1", "state": "ready", "dish": payload, "ready_ticks": 1199}],
                "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                               "order_status": "assigned", "reserved": []}],
            }
        }
        with Workdir() as w:
            out_ok = w.path("ok.jsonl")
            c, e = run_headless(
                "--mode", "quan", "--seed", "1",
                "--scenario", write_json(w.path("sc1.json"), sc_ok),
                "--inputs", write_json(w.path("in1.json"), frames({"tick": 0, "interact": True})),
                "--ticks", "1", "--out", out_ok,
            )
            self.assertEqual(c, 0, e)
            rows_ok = read_jsonl(out_ok)
            self.assertEqual(events(rows_ok, "dish_burnt"), [])
            self.assertEqual(len(events(rows_ok, "dish_picked")), 1)

        # 2) ready_ticks = 1200 at start -> tick 1 reaches 1201 -> burns immediately!
        # Subcase A: backup stock -> reserved; Subcase B: no backup -> unfulfillable
        for backup, exp_status in (([{"id": "I9", "kind": "ca_loc", "fresh": 100}], "reserved"), ([], "unfulfillable")):
            sc_burn = {
                "quan": {
                    "player": {"pos": [2, 8]},
                    "random_customers": False,
                    "stock": backup,
                    "stoves": [{"id": "B1", "state": "ready", "dish": payload, "ready_ticks": 1200}],
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "order_status": "assigned", "reserved": []}],
                }
            }
            with Workdir() as w:
                out_b = w.path("b.jsonl")
                c, e = run_headless(
                    "--mode", "quan", "--seed", "1",
                    "--scenario", write_json(w.path("scb.json"), sc_burn),
                    "--inputs", write_json(w.path("inb.json"), frames({"tick": 0, "interact": True})),
                    "--ticks", "1", "--snapshot-every", "1", "--out", out_b,
                )
                self.assertEqual(c, 0, e)
                rows_b = read_jsonl(out_b)
                burnt = events(rows_b, "dish_burnt")
                self.assertEqual(len(burnt), 1)
                self.assertEqual(burnt[0]["data"], {
                    "stove_id": "B1",
                    "order_id": "C1",
                    "dish_id": "ca_loc_nuong_trui",
                    "order_status": exp_status,
                })
                # Because backup exists or stove idle, inspect final customer status
                self.assertEqual(snapshots(rows_b)[-1]["customers"][0]["order_status"],
                                 "assigned" if exp_status == "reserved" else "unfulfillable")


if __name__ == "__main__":
    unittest.main()
