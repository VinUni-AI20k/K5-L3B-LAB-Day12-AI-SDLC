"""Kiểm chứng Phase 1 qua headless_cmd, JSONL và file kho (PRD-0 B, D–G)."""

import json
import unittest
from pathlib import Path

from helpers import ROOT, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


TUNING = json.loads((Path(ROOT) / "game.contract.json").read_text(encoding="utf-8"))["tuning"]
GATHER = TUNING["gather"]
QUAN = TUNING["quan"]
DISH = "ca_loc_nuong_trui"


class Phase1Integration(unittest.TestCase):
    def setUp(self):
        self.work = self.enterContext(Workdir())

    def _run(self, mode, ticks, output, *extra):
        code, stderr = run_headless(
            "--mode", mode, "--seed", "42", "--ticks", str(ticks), "--out", self.work.path(output), *extra
        )
        self.assertEqual(code, 0, stderr)
        return read_jsonl(self.work.path(output))

    def _gather(self, scenario, *inputs, ticks=1, name="gather"):
        scenario_path = write_json(self.work.path(f"{name}-scenario.json"), {"gather": scenario})
        input_path = write_json(self.work.path(f"{name}-inputs.json"), frames(*inputs))
        inventory = Path(self.work.path(f"{name}-inventory.json"))
        rows = self._run(
            "gather", ticks, f"{name}.jsonl", "--scenario", scenario_path,
            "--inputs", input_path, "--inventory-out", str(inventory),
        )
        return rows, inventory

    def _assert_handoff(self, rows, inventory, reason, items, quan_output="quan.jsonl"):
        expected = {"items": items}
        self.assertEqual([event["data"] for event in events(rows, "gather_end")],
                         [{"reason": reason, "inventory": expected}])
        self.assertEqual(rows[-1]["reason"], reason)
        self.assertTrue(inventory.is_file(), "gather_end phải ghi file kho")
        self.assertEqual(json.loads(inventory.read_text(encoding="utf-8")), expected)
        quan = self._run("quan", 0, quan_output, "--inventory", str(inventory))
        initial = snapshots(quan)[0]
        self.assertEqual(initial["tick"], 0)
        self.assertEqual(initial["stock"], items)

    def test_dock_o_buoc_cuoi_va_kho_tat_dinh(self):
        dock = GATHER["dock_pos"]
        scenario = {
            "player": {"pos": dock},
            "hold": ["ca_loc", "bong_sung", "bong_sung"],
            "nodes": [{"id": "N1", "kind": "bong_sung", "pos": dock}],
            "time_left_ticks": 1,
        }
        outputs = []
        for name in ("first", "second"):
            rows, inventory = self._gather(scenario, {"tick": 0, "interact": True}, name=name)
            self.assertEqual([(row["tick"], row["name"]) for row in events(rows)], [(1, "gather_end")])
            self._assert_handoff(rows, inventory, "docked", {"bong_sung": 2, "ca_loc": 1}, f"{name}-quan.jsonl")
            outputs.append((
                Path(self.work.path(f"{name}.jsonl")).read_bytes(),
                inventory.read_bytes(),
                Path(self.work.path(f"{name}-quan.jsonl")).read_bytes(),
            ))
        self.assertEqual(outputs[0], outputs[1])

    def test_tick_limit_giu_nguyen_file_kho_da_co(self):
        inventory = Path(self.work.path("gather-inventory.json"))
        before = b'{ "items": { "ca_loc": 4 } }\n'
        inventory.write_bytes(before)
        rows, _ = self._gather({"time_left_ticks": 2})
        self.assertEqual(events(rows, "gather_end"), [])
        self.assertEqual(rows[-1]["reason"], "tick_limit")
        self.assertEqual(inventory.read_bytes(), before)

    def test_hai_nut_vua_moc_lai_o_buoc_cuoi_roi_chuyen_kho(self):
        scenario = {
            "player": {"pos": [20, 0]},
            "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0], "regrow_ticks": 1}],
            "time_left_ticks": 1,
        }
        rows, inventory = self._gather(scenario, {"tick": 0, "interact": True})
        self.assertEqual([(row["tick"], row["name"]) for row in events(rows)],
                         [(1, "node_regrown"), (1, "gather"), (1, "gather_end")])
        self._assert_handoff(rows, inventory, "time", {"bong_sung": GATHER["node_yield"]})
        self.assertEqual(events(rows, "gather")[0]["data"],
                         {"node_id": "N1", "kind": "bong_sung", "amount": GATHER["node_yield"]})

    def test_bat_ca_o_buoc_cuoi_uu_tien_id_va_chuyen_kho(self):
        pos = [20, 5]
        scenario = {
            "player": {"pos": pos},
            "fish": [{"id": "F10", "kind": "ca_linh", "pos": pos}, {"id": "F2", "kind": "ca_loc", "pos": pos}],
            "time_left_ticks": 1,
        }
        rows, inventory = self._gather(scenario, {"tick": 0, "catch": True})
        self.assertEqual([(row["tick"], row["name"]) for row in events(rows)],
                         [(1, "fish_caught"), (1, "gather_end")])
        amount = GATHER["fish_yield"]["ca_loc"]
        self.assertEqual([fish["id"] for fish in snapshots(rows)[-1]["fish"]], ["F10"])
        self._assert_handoff(rows, inventory, "time", {"ca_loc": amount})
        self.assertEqual(events(rows, "fish_caught")[0]["data"], {"fish_id": "F2", "kind": "ca_loc", "yield": amount})

    def test_gio_thieu_cho_giu_ca_va_khong_dat_hoi_chieu(self):
        pos = [20, 5]
        hold = ["bong_sung"] * (GATHER["hold_capacity"] - 1)
        scenario = {
            "player": {"pos": pos},
            "hold": hold,
            "fish": [{"id": "F1", "kind": "ca_linh", "pos": pos}, {"id": "F2", "kind": "ca_loc", "pos": pos}],
        }
        rows, _ = self._gather(scenario, {"tick": 0, "catch": True})
        self.assertEqual(events(rows, "fish_caught"), [])
        final = snapshots(rows)[-1]
        self.assertEqual(final["hold"], hold)
        self.assertEqual([fish["id"] for fish in final["fish"]], ["F1", "F2"])
        self.assertEqual(final["player"]["catch_cd_ticks"], 0)
        self.assertEqual([row["data"] for row in events(rows, "hold_full")],
                         [{"action": "catch", "fish_id": "F1", "required": GATHER["fish_yield"]["ca_linh"], "free": 1}])

    def test_oxygen_empty_co_payload_theo_contract(self):
        rows, _ = self._gather({"player": {"pos": [20, 5], "oxygen_ticks": 1}})
        self.assertEqual([(row["tick"], row["data"]) for row in events(rows, "oxygen_empty")],
                         [(1, {"oxygen_ticks": 0})])

    def test_ngat_bo_gio_theo_lifo_va_xuat_kho_rong(self):
        hold = ["ca_loc", "ca_linh", "bong_sung"]
        scenario = {
            "player": {"pos": [20, 5], "oxygen_ticks": 0, "hp": 1,
                       "zero_oxy_ticks": GATHER["choke_interval_ticks"] - 1},
            "hold": hold,
        }
        rows, inventory = self._gather(scenario)
        self._assert_handoff(rows, inventory, "fainted", {})
        self.assertEqual([(row["tick"], row["name"]) for row in events(rows)],
                         [(1, "choke"), (1, "faint"), (1, "gather_end")])
        self.assertEqual(events(rows, "faint")[0]["data"], {"cause": "choke", "hp": 0, "lost": hold[::-1]})

    def test_quan_goi_mon_theo_kho_va_lich_khach(self):
        first_tick = QUAN["first_customer_tick"]
        recipe = TUNING["menu"][DISH]["recipe"]
        for items, event_name in ((recipe, "customer_arrived"), ({}, "no_dish")):
            with self.subTest(event=event_name):
                inventory = write_json(self.work.path(f"{event_name}.json"), {"items": items})
                rows = self._run("quan", first_tick, "quan.jsonl", "--inventory", inventory)
                order_events = [row for row in events(rows) if row["name"] in {"customer_arrived", "no_dish"}]
                self.assertEqual([(row["tick"], row["name"]) for row in order_events], [(first_tick, event_name)])
                final = snapshots(rows)[-1]
                self.assertEqual(final["stock"], items)
                if items:
                    table_id = QUAN["tables"][0]["id"]
                    customer, = final["customers"]
                    self.assertEqual(order_events[0]["data"], {
                        "order_id": customer["id"], "table_id": table_id, "dish_id": DISH,
                    })
                    self.assertEqual(customer["order_tick"], first_tick)
                    self.assertEqual(customer["reserved"], recipe)
                else:
                    self.assertEqual(order_events[0]["data"], {})
                    self.assertEqual(final["customers"], [])

    def test_quan_phuc_vu_o_tick_het_kien_nhan_va_dong_ca(self):
        table = QUAN["tables"][0]
        price = TUNING["menu"][DISH]["price"]
        order_id = "C1"
        scenario = write_json(self.work.path("closing-scenario.json"), {"quan": {
            "player": {"pos": table["pos"]},
            "random_customers": False,
            "time_left_ticks": 1,
            "hand": {"order_id": order_id, "dish_id": DISH, "base_price": price},
            "customers": [{"id": order_id, "table_id": table["id"], "dish_id": DISH,
                           "state": "waiting", "order_status": "assigned", "patience_ticks_left": 1,
                           "reserved": {}}],
        }})
        inputs = write_json(self.work.path("closing-inputs.json"), frames({"tick": 0, "interact": True}))
        rows = self._run("quan", 1, "quan.jsonl", "--scenario", scenario, "--inputs", inputs)
        self.assertEqual([(row["tick"], row["name"]) for row in events(rows)],
                         [(1, "served"), (1, "paid"), (1, "quan_end")])
        self.assertEqual(events(rows, "served")[0]["data"], {
            "order_id": order_id, "table_id": table["id"], "dish_id": DISH,
            "patience_ticks_left": 0, "base_price": price, "tip": 0,
        })
        self.assertEqual(events(rows, "paid")[0]["data"], {
            "order_id": order_id, "table_id": table["id"], "base_price": price,
            "tip": 0, "amount": price, "reason": "closing",
        })
        self.assertEqual(rows[-1]["money"], price)
        self.assertEqual(rows[-1]["earned"], price)
        self.assertEqual(rows[-1]["reputation"], QUAN["reputation_initial"])
