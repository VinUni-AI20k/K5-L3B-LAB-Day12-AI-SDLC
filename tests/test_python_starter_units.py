"""Unit test của khung PYTHON trong starter (ids, inputs, Session). Nếu nhóm thay bằng ngôn ngữ khác, XÓA file này
(và viết unit test tương đương bằng ngôn ngữ của nhóm); test hộp đen test_smoke_p1.py vẫn dùng nguyên."""

import unittest

from chonoi.errors import BadInput
from chonoi.ids import IdAllocator, id_key, sort_by_id
from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer, LiveInputs, load_frames
from chonoi.runner import Session

from helpers import Workdir, frames, write_json


class Units(unittest.TestCase):
    def test_id_sorting(self):
        self.assertEqual([e["id"] for e in sort_by_id([{"id": "F10"}, {"id": "F2"}, {"id": "B1"}])], ["B1", "F2", "F10"])
        self.assertLess(id_key("F2"), id_key("F10"))

    def test_id_allocator_continues_after_max(self):
        a = IdAllocator()
        a.reserve("F3")
        a.reserve("F10")
        self.assertEqual(a.new("F"), "F11")
        self.assertEqual(a.new("F"), "F12")
        self.assertEqual(a.new("S"), "S1")

    def test_input_edges_and_inherit(self):
        with Workdir() as w:
            p = write_json(w.path("i.json"), frames({"tick": 1, "interact": True}, {"tick": 2, "move": [1, 1]}, {"tick": 3, "interact": False}, {"tick": 4, "interact": True}))
            pl = InputPlayer(load_frames(p))
            self.assertFalse(pl.advance(0).pressed("interact"))
            self.assertTrue(pl.advance(1).pressed("interact"))
            s2 = pl.advance(2)
            self.assertFalse(s2.pressed("interact"), "giữ true không lặp lại")
            self.assertAlmostEqual(s2.move[0] ** 2 + s2.move[1] ** 2, 1.0)
            pl.advance(3)
            self.assertTrue(pl.advance(4).pressed("interact"))
            self.assertEqual(pl.advance(5).move, s2.move, "move giữ giá trị cũ khi vắng frame")

    def test_bad_frames_raise(self):
        with Workdir() as w:
            with self.assertRaises(BadInput):
                load_frames(write_json(w.path("i.json"), frames({"tick": 0, "move": [2, 0]})))

    def test_catch_is_a_v10_button_and_attack_is_not(self):
        with Workdir() as w:
            load_frames(write_json(w.path("i.json"), frames({"tick": 0, "catch": True})))
            with self.assertRaises(BadInput):
                load_frames(write_json(w.path("j.json"), frames({"tick": 0, "attack": True})))

    def test_live_inputs_keep_fast_tap_edge(self):
        li = LiveInputs()
        li.set(interact=True)
        li.set(interact=False)  # bấm và nhả giữa hai tick: vẫn phải thấy một cạnh lên
        self.assertTrue(li.advance().pressed("interact"))
        self.assertFalse(li.advance().pressed("interact"))
        li.set(move=[1, 1], catch=True)
        st = li.advance()
        self.assertTrue(st.pressed("catch"))
        self.assertAlmostEqual(st.move[0] ** 2 + st.move[1] ** 2, 1.0)

    def test_session_steps_gather_and_dock(self):
        tuning = load_contract()["tuning"]
        # P3 [THAY THẾ]: giỏ chứa cá thể có id và độ tươi.
        s = Session("gather", tuning, {"hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100}]}, 1)
        self.assertEqual(s.snapshot()["tick"], 0)
        li = LiveInputs()
        self.assertEqual(s.step(li.advance()), [])
        li.set(interact=True)
        rows = s.step(li.advance())
        self.assertEqual([r["name"] for r in rows], ["gather_end"])
        self.assertTrue(s.done)
        self.assertEqual(s.snapshot()["tick"], 2)
        self.assertEqual(s.end_row()["reason"], "docked")



class FreshInventoryP3(unittest.TestCase):
    """Slice A validation works independently of the gather/quan migration."""
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_freshness_units_boundary_decay_and_id_ties(self):
        from chonoi.fresh import to_units, to_fresh, item_out, is_spoiled, decay_per_tick_u, freshest_first
        self.assertEqual(to_units(100), 24000)
        self.assertEqual(to_fresh(7200), 30)
        self.assertFalse(is_spoiled(7200, self.tuning))
        self.assertTrue(is_spoiled(7199, self.tuning))
        self.assertEqual(decay_per_tick_u(self.tuning, "gather"), 2)
        self.assertEqual(decay_per_tick_u(self.tuning, "quan"), 1)
        items = [{"id": i, "kind": "ca_loc", "fresh_u": u} for i, u in (("I10", 8000), ("I2", 8000), ("I1", 7199))]
        self.assertEqual([it["id"] for it in freshest_first(items)], ["I2", "I10", "I1"])
        self.assertEqual(item_out(items[-1])["fresh"], 29.995833)

    def test_inventory_atomic_roundtrip_every_unit_near_threshold(self):
        from chonoi.inventory import read_inventory, write_inventory
        from unittest.mock import patch
        import os
        items = [{"id": f"I{i}", "kind": "ca_loc", "fresh_u": u}
                 for i, u in ((10, 7199), (2, 7200), (1, 7201))]
        with Workdir() as w:
            path = w.path("inventory.json")
            write_inventory(path, items)
            self.assertEqual(read_inventory(path, self.tuning), sort_by_id(items))
            with open(path, "rb") as f:
                before = f.read()
            with patch("chonoi.inventory.os.replace", side_effect=OSError("replace failed")):
                with self.assertRaises(OSError):
                    write_inventory(path, [])
            with open(path, "rb") as f:
                self.assertEqual(f.read(), before)
            self.assertFalse(any(name.startswith(".inv-") for name in os.listdir(os.path.dirname(path))))

    def test_inventory_rejects_old_schema_and_invalid_individuals(self):
        from chonoi.inventory import read_inventory
        item = {"id": "I1", "kind": "ca_loc", "fresh": 30}
        bad = [{"items": {}}, {"items": {"ca_loc": 1}}, {"items": [], "extra": 1},
               {"items": [item, item]}, {"items": ["ca_loc"]}]
        for key, value in (("id", ""), ("id", 1), ("kind", "unknown"), ("kind", []),
                           ("fresh", True), ("fresh", -1), ("fresh", 101),
                           ("fresh", float("nan")), ("fresh", float("inf")), ("fresh", 10**1000)):
            bad.append({"items": [{**item, key: value}]})
        bad.append({"items": [{**item, "extra": 1}]})
        with Workdir() as w:
            for payload in bad:
                with self.subTest(payload=payload), self.assertRaises(BadInput):
                    read_inventory(write_json(w.path("bad.json"), payload), self.tuning)

    def test_scenario_normalizes_cargo_without_reordering_hold(self):
        from chonoi.scenario import load_scenario
        items = [{"id": "I10", "kind": "ca_loc", "fresh": 30},
                 {"id": "I2", "kind": "ca_linh", "fresh": 0}]
        with Workdir() as w:
            result = load_scenario(write_json(w.path("s.json"), {"gather": {"hold": items}}), "gather", self.tuning)
            self.assertEqual(result["hold"], items)
            self.assertIsInstance(result["hold"][0]["fresh"], float)
            for hold in (["ca_loc"], [items[0], items[0]]):
                with self.assertRaises(BadInput):
                    load_scenario(write_json(w.path("s.json"), {"gather": {"hold": hold}}), "gather", self.tuning)

    def test_scenario_reservation_ids_recipe_spoiled_shared_missing(self):
        from copy import deepcopy
        from chonoi.scenario import load_scenario
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": 30}]
        customer = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}
        block = {"stock": stock, "customers": [customer]}
        with Workdir() as w:
            def check(b):
                return load_scenario(write_json(w.path("s.json"), {"quan": b}), "quan", self.tuning)
            self.assertEqual(check(block)["customers"][0]["reserved"], ["I1"])
            missing = deepcopy(block); del missing["customers"][0]["reserved"]
            self.assertNotIn("reserved", check(missing)["customers"][0])
            for reserved in ({"ca_loc": 1}, ["I2"], ["I1", "I1"], [], None):
                bad = deepcopy(block); bad["customers"][0]["reserved"] = reserved
                with self.subTest(reserved=reserved), self.assertRaises(BadInput): check(bad)
            bad = deepcopy(block); bad["stock"][0]["fresh"] = 29
            with self.assertRaises(BadInput): check(bad)
            bad = deepcopy(block); bad["customers"].append({**customer, "id": "C2", "table_id": "T2"})
            with self.assertRaises(BadInput): check(bad)
            bad = deepcopy(block); bad["customers"][0]["order_status"] = "assigned"
            with self.assertRaises(BadInput): check(bad)

    def test_file_stock_reservations_resolve_before_sim_construction(self):
        from chonoi.scenario import load_scenario
        from chonoi.runner import build_sim
        from unittest.mock import patch
        block = {"customers": [{"id": "C1", "table_id": "T1",
                 "dish_id": "ca_loc_nuong_trui", "reserved": ["I10"]}]}
        stock = [{"id": "I10", "kind": "ca_loc", "fresh_u": 7200}]
        with Workdir() as w:
            scenario = load_scenario(write_json(w.path("s.json"), {"quan": block}), "quan", self.tuning)
        with patch("chonoi.runner.QuanSim") as quan:
            build_sim("quan", self.tuning, scenario, 1, stock)
            self.assertEqual(quan.call_args.args[3].new("I"), "I11")
            quan.reset_mock()
            for bad in ([], [{**stock[0], "fresh_u": 7199}]):
                with self.assertRaises(BadInput): build_sim("quan", self.tuning, scenario, 1, bad)
            quan.assert_not_called()

    def test_contract_freshness_keys_and_domains(self):
        from copy import deepcopy
        from chonoi.contract import validate_tuning
        for key, value in (("initial", -1), ("initial", 101), ("initial", True),
                           ("gather_decay_per_s", -1), ("quan_decay_per_s", float("inf")),
                           ("spoiled_below", float("nan")), ("unknown", 1)):
            tuning = deepcopy(self.tuning); tuning["freshness"][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(BadInput): validate_tuning(tuning)
        tuning = deepcopy(self.tuning); del tuning["freshness"]["initial"]
        with self.assertRaises(BadInput): validate_tuning(tuning)

    def test_runner_writes_inventory_once_and_never_before_end(self):
        from unittest.mock import Mock, patch
        from chonoi.runner import Session
        session = Session.__new__(Session)
        session.mode, session._inventory_written = "gather", False
        session.sim = Mock(done=False)
        with patch("chonoi.runner.write_inventory") as write:
            session.write_inventory_if_done("inventory.json"); write.assert_not_called()
            session.sim.done = True; session.sim.inventory_items.return_value = []
            session.write_inventory_if_done("inventory.json")
            session.write_inventory_if_done("inventory.json")
            write.assert_called_once_with("inventory.json", [])


if __name__ == "__main__":
    unittest.main()
