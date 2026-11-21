"""Phase 3, P3-01: độ tươi nguyên liệu trong giỏ gather (hao tươi, spoiled, LIFO, bàn giao ID)."""

import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import InputPlayer
from chonoi.runner import Session
from chonoi.scenario import load_scenario

from helpers import Workdir, write_json

DECAY_TICK = 0.5 / 60  # gather_decay_per_s / tick_hz


def item(ident, kind="ca_loc", fresh=100.0):
    return {"id": ident, "kind": kind, "fresh": fresh}


class GatherFreshness(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.g = self.tuning["gather"]

    def session(self, block, seed=1):
        fixture = {"nodes": [], "fish": [], "monsters": [], **block}
        return Session("gather", self.tuning, fixture, seed)

    @staticmethod
    def step(s, **pressed):
        return s.step(InputPlayer([{"tick": s.tick, **pressed}]).advance(s.tick))

    @staticmethod
    def idle(s, n):
        rows = []
        for _ in range(n):
            rows.extend(s.step(InputPlayer([]).advance(s.tick)))
        return rows

    def harvest_session(self, hold=None):
        block = {"player": {"pos": [20, 0]},
                 "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}]}
        if hold is not None:
            block["hold"] = hold
        return self.session(block)

    # --- tạo nguyên liệu ---------------------------------------------------------
    def test_hai_tao_ca_the_fresh_100_va_id_theo_thu_tu(self):
        s = self.harvest_session()
        rows = self.step(s, interact=True)
        self.assertIn("gather", [r["name"] for r in rows])
        self.assertEqual(s.sim.hold_items, [item("I1", "bong_sung", 100.0)])

    def test_bat_ca_tao_moi_ca_the_co_id_rieng(self):
        s = self.session({"player": {"pos": [20, 5]},
                          "fish": [{"id": "F2", "kind": "ca_linh", "pos": [21, 5], "heading_deg": 0}]})
        self.step(s, catch=True)
        ids = [u["id"] for u in s.sim.hold_items]
        self.assertEqual(len(ids), self.g["fish_yield"]["ca_linh"])
        self.assertEqual(len(set(ids)), len(ids))
        self.assertTrue(all(u["fresh"] == 100.0 for u in s.sim.hold_items))

    def test_hang_vua_nhat_chua_hao_den_tick_sau(self):
        s = self.harvest_session()
        self.step(s, interact=True)
        self.assertEqual(s.sim.hold_items[0]["fresh"], 100.0)
        self.idle(s, 1)
        self.assertAlmostEqual(s.sim.hold_items[0]["fresh"], 100.0 - DECAY_TICK, places=9)

    # --- hao tươi ----------------------------------------------------------------
    def test_hao_0_5_diem_moi_giay(self):
        s = self.session({"hold": [item("I1", fresh=90.0)]})
        self.idle(s, 60)
        self.assertAlmostEqual(s.sim.hold_items[0]["fresh"], 89.5, places=9)

    def test_san_0_khong_am(self):
        s = self.session({"hold": [item("I1", fresh=0.001)]})
        self.idle(s, 5)
        self.assertEqual(s.sim.hold_items[0]["fresh"], 0.0)

    # --- ngưỡng ươn ----------------------------------------------------------------
    def test_fresh_30_ươn_o_tick_1_dung_mot_lan(self):
        s = self.session({"hold": [item("I1", "ca_linh", 30)]})
        rows = self.idle(s, 1)
        spoiled = [r for r in rows if r["name"] == "spoiled"]
        self.assertEqual([(r["tick"], r["data"]) for r in spoiled],
                         [(1, {"item_id": "I1", "kind": "ca_linh", "location": "hold"})])
        self.assertEqual([r for r in self.idle(s, 300) if r["name"] == "spoiled"], [])

    def test_fresh_29_9_khong_phat_spoiled(self):
        s = self.session({"hold": [item("I1", "ca_linh", 29.9)]})
        self.assertEqual([r for r in self.idle(s, 10) if r["name"] == "spoiled"], [])

    def test_bien_nguong_chinh_xac_theo_gia_tri_that(self):
        # 30.5 hao 1/120 mỗi tick: tick 60 còn đúng 30.0 (chưa ươn), tick 61 xuống dưới 30
        s = self.session({"hold": [item("I1", fresh=30.5)]})
        self.assertEqual([r for r in self.idle(s, 60) if r["name"] == "spoiled"], [])
        self.assertEqual([r["tick"] for r in self.idle(s, 1) if r["name"] == "spoiled"], [61])

    def test_nhieu_ca_the_vuot_nguong_cung_luc_sap_theo_id(self):
        s = self.session({"hold": [item("I2", fresh=30), item("I1", fresh=30)]})
        spoiled = [r["data"]["item_id"] for r in self.idle(s, 1) if r["name"] == "spoiled"]
        self.assertEqual(spoiled, ["I1", "I2"])

    def test_hang_uon_van_chiem_cho_nen_giỏ_day_khong_nhan_them(self):
        hold = [item(f"I{i}", fresh=5.0) for i in range(1, self.g["hold_capacity"] + 1)]
        s = self.session({"player": {"pos": [20, 0]},
                          "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}],
                          "hold": hold})
        self.idle(s, 1)
        self.assertEqual(len(s.sim.hold_items), self.g["hold_capacity"])
        rows = self.step(s, interact=True)
        self.assertIn("hold_full", [r["name"] for r in rows])
        self.assertEqual(len(s.sim.hold_items), self.g["hold_capacity"])

    # --- LIFO khi ngất ------------------------------------------------------------
    def test_ngat_mat_het_theo_lifo_voi_object(self):
        s = self.session({"player": {"pos": [30, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                          "hold": [item("I1", "ca_loc", 80.0), item("I2", "ca_linh", 70.0)]})
        rows = self.idle(s, 1)
        faint = [r for r in rows if r["name"] == "faint"][0]["data"]
        self.assertEqual([u["id"] for u in faint["lost"]], ["I2", "I1"])
        self.assertEqual(s.sim.hold_items, [])

    # --- bàn giao ----------------------------------------------------------------
    def test_ban_giao_giu_id_va_fresh_sau_hao_mot_tick(self):
        s = self.session({"player": {"pos": [2, 0]}, "hold": [item("I7", "ca_loc", 55.5)]})
        rows = self.step(s, interact=True)
        end = [r for r in rows if r["name"] == "gather_end"][0]["data"]
        self.assertEqual(end["reason"], "docked")
        items = end["inventory"]["items"]
        self.assertEqual([(i["id"], i["kind"]) for i in items], [("I7", "ca_loc")])
        self.assertAlmostEqual(items[0]["fresh"], 55.5 - DECAY_TICK, places=9)

    def test_snapshot_hold_la_mang_object(self):
        s = self.session({"hold": [item("I1", "ca_loc", 80.0)]})
        self.assertEqual(s.sim.snapshot()["hold"], [item("I1", "ca_loc", 80.0)])

    # --- validation scenario -----------------------------------------------------
    def test_scenario_nhan_hold_dang_object(self):
        with Workdir() as w:
            path = write_json(w.path("sc.json"), {"gather": {"hold": [item("I9", "keo_neo", 12)]}})
            self.assertEqual(load_scenario(path, "gather", self.tuning)["hold"][0]["id"], "I9")

    def test_scenario_tu_choi_fresh_sai_va_id_trung(self):
        with Workdir() as w:
            bad = [
                {"gather": {"hold": [item("I1", fresh=101)]}},
                {"gather": {"hold": [item("I1", fresh=-1)]}},
                {"gather": {"hold": [{"id": "I1", "kind": "ca_loc"}]}},
                {"gather": {"hold": [item("I1", fresh=50), item("I1", "ca_linh", 50)]}},
            ]
            for i, body in enumerate(bad):
                path = write_json(w.path(f"bad{i}.json"), body)
                with self.assertRaises(BadInput, msg=str(body)):
                    load_scenario(path, "gather", self.tuning)


if __name__ == "__main__":
    unittest.main()
