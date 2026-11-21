"""Test nền Test Contract v1.2 (LeBao403, Integrator): đơn vị độ tươi, cá thể, file kho cá thể, manifest freshness,
scenario hold/stock dạng cá thể, phần khung của GatherSim/QuanSim. Ticket-03 mục 1.

Manifest còn ở 1.1 trong lúc chuyển, nên test dựng tuning v1.2 trong bộ nhớ (thêm khối freshness).
Luật của từng lát (hao tươi giỏ, giữ chỗ theo id, hao kho, giá theo tươi) có test riêng của chủ lát.

Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -p "test_p3_fresh_schema.py" -v
"""

import copy
import json
import unittest

from chonoi import fresh
from chonoi.contract import FRESHNESS_V12, load_contract, validate_freshness
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inventory import encode, read_inventory, write_inventory
from chonoi.rng import Streams
from chonoi.scenario import load_scenario
from chonoi.sim.gather import GatherSim
from chonoi.sim.quan import QuanSim
from helpers import Workdir, write_json

T11 = load_contract()["tuning"]
T12 = dict(copy.deepcopy(T11), freshness=dict(FRESHNESS_V12))


def item(iid, kind="ca_linh", f=100):
    return {"id": iid, "kind": kind, "fresh": f}


class Units(unittest.TestCase):
    def test_hang_so_don_vi(self):
        c = fresh.cfg(T12)
        self.assertEqual(c, {"initial_u": 24000, "gather_decay_u": 2, "quan_decay_u": 1, "spoiled_u": 7200})
        self.assertFalse(fresh.enabled(T11))
        self.assertTrue(fresh.enabled(T12))

    def test_to_units_khong_doi_phia_nguong(self):
        self.assertEqual(fresh.to_units(30), 7200)
        self.assertLess(fresh.to_units(29.999), 7200)
        self.assertGreaterEqual(fresh.to_units(30.001), 7200)
        self.assertEqual(fresh.to_units(97.5), 23400)

    def test_decay_phat_vua_uon_mot_lan_theo_id_va_kep_day(self):
        items = [fresh.from_public(item("I10", f=30)), fresh.from_public(item("I2", f=30)),
                 fresh.from_public(item("I3", f=50))]
        newly = fresh.decay(items, 2, T12)
        self.assertEqual([it["id"] for it in newly], ["I2", "I10"])
        self.assertEqual(fresh.decay(items, 2, T12), [])  # không phát lại
        low = [{"id": "I1", "kind": "ca_loc", "u": 1}]
        fresh.decay(low, 2, T12)
        self.assertEqual(low[0]["u"], 0)

    def test_new_item_noi_tiep_id_va_public(self):
        ids = IdAllocator()
        ids.reserve("I5")
        it = fresh.new_item(ids, "ca_loc", T12)
        self.assertEqual(fresh.public(it), {"id": "I6", "kind": "ca_loc", "fresh": 100.0})
        self.assertEqual(fresh.out(["ca_loc", it]), ["ca_loc", {"id": "I6", "kind": "ca_loc", "fresh": 100.0}])


class InventoryFile(unittest.TestCase):
    def test_ghi_doc_v12_giu_dung_gia_tri_va_sap_theo_id(self):
        items = [{"id": "I10", "kind": "ca_loc", "u": 23998}, {"id": "I2", "kind": "ca_linh", "u": 7200}]
        with Workdir() as w:
            p = w.path("k.json")
            write_inventory(p, items, "1.2")
            with open(p, encoding="utf-8") as f:
                raw = json.load(f)
            self.assertEqual([x["id"] for x in raw["items"]], ["I2", "I10"])
            self.assertEqual(read_inventory(p, "1.2"), sorted(items, key=lambda x: int(x["id"][1:])))
            write_inventory(p, [], "1.2")
            self.assertEqual(read_inventory(p, "1.2"), [])

    def test_v12_tu_choi_kho_dem_va_sai_schema(self):
        bad = ({"items": {"ca_loc": 1}},                                   # kho đếm
               {"items": [item("I1"), item("I1")]},                        # id trùng
               {"items": [item("I1", f=100.5)]},                           # fresh ngoài miền
               {"items": [item("I1", f=-1)]},
               {"items": [item("I1", kind="ca_map")]},                      # kind lạ
               {"items": [dict(item("I1"), extra=1)]},                     # khóa lạ
               {"items": [item("")]},                                      # id rỗng
               {"items": [], "x": 1})                                      # khóa gốc lạ
        with Workdir() as w:
            for b in bad:
                with self.assertRaises(BadInput, msg=b):
                    read_inventory(write_json(w.path("k.json"), b), "1.2")

    def test_v11_giu_kho_dem(self):
        with Workdir() as w:
            p = write_json(w.path("k.json"), {"items": {"ca_loc": 2}})
            self.assertEqual(read_inventory(p, "1.1"), {"ca_loc": 2})
            with self.assertRaises(BadInput):
                read_inventory(write_json(w.path("k2.json"), {"items": [item("I1")]}), "1.1")
        self.assertEqual(encode(["ca_loc", "ca_loc"], "1.1"), {"ca_loc": 2})
        with self.assertRaises(BadInput):
            encode({"ca_loc": 1}, "1.2")


class Manifest(unittest.TestCase):
    def test_freshness_bat_buoc_o_12_va_cam_o_11(self):
        validate_freshness("1.2", T12)
        validate_freshness("1.1", T11)
        with self.assertRaises(BadInput):
            validate_freshness("1.2", T11)
        with self.assertRaises(BadInput):
            validate_freshness("1.1", T12)
        with self.assertRaises(BadInput):
            validate_freshness("1.2", dict(T11, freshness=dict(FRESHNESS_V12, spoiled_below=25)))


class ScenarioV12(unittest.TestCase):
    def load(self, mode, block, tuning=T12):
        with Workdir() as w:
            return load_scenario(write_json(w.path("sc.json"), {mode: block}), mode, tuning)

    def test_hold_va_stock_la_ca_the(self):
        self.load("gather", {"hold": [item("I1"), item("I2", "ca_loc", 30)]})
        self.load("quan", {"stock": [item("I1", "bong_sung", 80)]})

    def test_hold_sai_schema_ma_2(self):
        for hold in (["ca_loc"], [item("I1"), item("I1")], [item("I1", f=101)],
                     [item(f"I{i}") for i in range(1, T12["gather"]["hold_capacity"] + 2)]):
            with self.assertRaises(BadInput, msg=hold):
                self.load("gather", {"hold": hold})
        with self.assertRaises(BadInput):
            self.load("quan", {"stock": {"ca_loc": 1}})

    def test_v11_van_nhan_dang_cu(self):
        self.load("gather", {"hold": ["ca_loc"]}, T11)
        with self.assertRaises(BadInput):
            self.load("gather", {"hold": [item("I1")]}, T11)


class SimFramework(unittest.TestCase):
    def test_gather_v12_hold_ca_the_snapshot_va_kho_ban_giao(self):
        ids = IdAllocator()
        g = GatherSim(T12, {"hold": [item("I7", "ca_loc", 50), item("I3")], "random_fish": False, "monsters": []},
                      Streams(1), ids)
        self.assertEqual(g.snapshot()["hold"], [item("I7", "ca_loc", 50.0), item("I3", "ca_linh", 100.0)])
        self.assertEqual([x["id"] for x in g.inventory_items()], ["I3", "I7"])  # file kho sắp theo id
        self.assertEqual(ids.new("I"), "I8")  # id fixture được reserve

    def test_gather_v12_lost_khi_ngat_la_ca_the_lifo(self):
        g = GatherSim(T12, {"hold": [item("I1"), item("I2", "ca_loc")], "random_fish": False, "monsters": [],
                            "player": {"pos": [50, 20], "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": 59}},
                      Streams(1), IdAllocator())
        from chonoi.inputs import InputState
        ev = dict(g.step(InputState((0.0, 0.0), {}, set())))
        self.assertEqual(ev["faint"]["lost"], [item("I2", "ca_loc", 100.0), item("I1", "ca_linh", 100.0)])
        self.assertEqual(ev["gather_end"]["inventory"], {"items": []})

    def test_gather_v11_khong_doi(self):
        g = GatherSim(T11, {"hold": ["ca_loc", "ca_loc"], "random_fish": False}, Streams(1), IdAllocator())
        self.assertEqual((g.snapshot()["hold"], g.inventory_items()), (["ca_loc", "ca_loc"], {"ca_loc": 2}))

    def test_quan_v12_stock_ca_the(self):
        ids = IdAllocator()
        q = QuanSim(T12, {"stock": [item("I9", "bong_sung", 80), item("I4", "bong_sung")]}, Streams(1), ids)
        self.assertEqual([x["id"] for x in q.snapshot()["stock"]], ["I4", "I9"])
        self.assertEqual(q.snapshot()["stock"][1]["fresh"], 80.0)
        self.assertEqual(ids.new("I"), "I10")
        inv = [{"id": "I1", "kind": "ca_loc", "u": 24000}]
        q2 = QuanSim(T12, {}, Streams(1), IdAllocator(), inventory=inv)
        self.assertEqual(q2.snapshot()["stock"], [item("I1", "ca_loc", 100.0)])


if __name__ == "__main__":
    unittest.main()
