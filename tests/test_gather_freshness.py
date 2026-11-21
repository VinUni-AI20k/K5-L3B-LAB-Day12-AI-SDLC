"""Phase 3, P3-01: độ tươi nguyên liệu trong giỏ gather (hao tươi, ngưỡng ươn, LIFO, bàn giao ID)."""

import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import InputPlayer
from chonoi.runner import Session
from chonoi.scenario import load_scenario

from helpers import Workdir, write_json

TICK = 60.0


class GatherFreshness(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.g = self.tuning["gather"]
        self.decay = self.g["fresh_decay_per_s"] / TICK

    def session(self, block, seed=1):
        fixture = {"nodes": [], "fish": [], **block}
        return Session("gather", self.tuning, fixture, seed)

    def step(self, s, **pressed):
        frame = {"tick": s.tick, **pressed}
        return s.step(InputPlayer([frame]).advance(s.tick))

    def idle(self, s, n):
        rows = []
        for _ in range(n):
            rows.extend(s.step(InputPlayer([]).advance(s.tick)))
        return rows

    def harvest_session(self, hold=None, extra=None):
        block = {"player": {"pos": [20, 0]},
                 "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}]}
        if hold is not None:
            block["hold"] = hold
        block.update(extra or {})
        return self.session(block)

    # --- tạo nguyên liệu -------------------------------------------------------
    def test_hai_tao_ca_the_fresh_100_va_id_rieng(self):
        s = self.harvest_session()
        rows = self.step(s, interact=True)
        self.assertEqual(s.sim.hold, [{"id": "NL1", "kind": "bong_sung", "fresh": 100.0, "spoiled": False}])
        self.assertIn("gather", [r["name"] for r in rows])

    def test_bat_ca_tao_moi_ca_the_co_id_rieng(self):
        s = self.session({"player": {"pos": [20, 5]},
                          "fish": [{"id": "F2", "kind": "ca_linh", "pos": [21, 5], "heading_deg": 0}]})
        self.step(s, catch=True)
        ids = [u["id"] for u in s.sim.hold]
        self.assertEqual(len(ids), self.g["fish_yield"]["ca_linh"])
        self.assertEqual(len(set(ids)), len(ids))
        self.assertTrue(all(u["fresh"] == 100.0 for u in s.sim.hold))

    # --- hao tươi ---------------------------------------------------------------
    def test_hao_tuoi_bat_dau_tu_tick_sau_khi_thu_thap(self):
        s = self.harvest_session()
        self.step(s, interact=True)
        self.assertEqual(s.sim.hold[0]["fresh"], 100.0, "tick nhặt chưa hao")
        self.idle(s, 1)
        self.assertAlmostEqual(s.sim.hold[0]["fresh"], 100.0 - self.decay, places=9)

    def test_hao_0_5_diem_moi_giay(self):
        s = self.session({"hold": [{"id": "NL1", "kind": "ca_loc", "fresh": 90.0}]})
        self.idle(s, 60)
        self.assertAlmostEqual(s.sim.hold[0]["fresh"], 89.5, places=6)

    # --- ngưỡng ươn -------------------------------------------------------------
    def test_duoi_30_phat_spoiled_dung_mot_lan(self):
        s = self.session({"hold": [{"id": "NL1", "kind": "ca_loc", "fresh": 30.005}]})
        rows = self.idle(s, 600)
        spoiled = [r for r in rows if r["name"] == "spoiled"]
        self.assertEqual(len(spoiled), 1)
        self.assertEqual(spoiled[0]["data"]["id"], "NL1")
        self.assertLess(spoiled[0]["data"]["fresh"], 30)
        self.assertTrue(s.sim.hold[0]["spoiled"])

    def test_bien_nguong_30(self):
        # 30.5 hao 0.5/120 mỗi tick: sau 60 tick còn đúng 30.0 (chưa ươn), tick 61 xuống dưới 30
        s = self.session({"hold": [{"id": "NL1", "kind": "ca_loc", "fresh": 30.5}]})
        self.assertEqual([r for r in self.idle(s, 60) if r["name"] == "spoiled"], [])
        self.assertFalse(s.sim.hold[0]["spoiled"])
        self.assertEqual([r["tick"] for r in self.idle(s, 1) if r["name"] == "spoiled"], [61])

    def test_hang_uon_van_chiem_cho_va_lam_day_gio(self):
        hold = [{"id": f"NL{i}", "kind": "ca_loc", "fresh": 5.0} for i in range(1, 13)]
        s = self.session({"player": {"pos": [20, 0]},
                          "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}],
                          "hold": hold})
        self.idle(s, 1)
        self.assertTrue(all(u["spoiled"] for u in s.sim.hold))
        self.assertEqual(len(s.sim.hold), self.g["hold_capacity"])
        rows = self.step(s, interact=True)  # giỏ đầy: hàng ươn không được đẩy ra để nhường chỗ
        self.assertIn("hold_full", [r["name"] for r in rows])
        self.assertEqual(len(s.sim.hold), self.g["hold_capacity"])

    # --- LIFO khi làm rơi ---------------------------------------------------------
    def test_lam_roi_theo_lifo(self):
        s = self.session({"hold": [{"id": "NL1", "kind": "ca_loc", "fresh": 80.0},
                                   {"id": "NL2", "kind": "ca_linh", "fresh": 70.0},
                                   {"id": "NL3", "kind": "bong_sung", "fresh": 60.0}]})
        events = []
        dropped = s.sim._drop_lifo(2, "test", events)
        self.assertEqual([u["id"] for u in dropped], ["NL3", "NL2"])
        self.assertEqual([u["id"] for u in s.sim.hold], ["NL1"])
        self.assertEqual(events[0][0], "dropped")
        self.assertEqual([u["id"] for u in events[0][1]["units"]], ["NL3", "NL2"])

    def test_ngat_mat_het_giu_thu_tu_lifo(self):
        s = self.session({"player": {"pos": [30, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                          "hold": [{"id": "NL1", "kind": "ca_loc", "fresh": 80.0},
                                   {"id": "NL2", "kind": "ca_linh", "fresh": 70.0}]})
        rows = self.idle(s, 1)
        faint = [r for r in rows if r["name"] == "faint"][0]
        self.assertEqual([u["id"] for u in faint["data"]["lost"]], ["NL2", "NL1"])
        self.assertEqual(s.sim.hold, [])

    # --- bàn giao ----------------------------------------------------------------
    def test_ban_giao_giu_dung_id_va_do_tuoi(self):
        s = self.session({"player": {"pos": [2, 0]},
                          "hold": [{"id": "NL7", "kind": "ca_loc", "fresh": 55.5}]})
        rows = self.step(s, interact=True)
        end = [r for r in rows if r["name"] == "gather_end"][0]
        self.assertEqual(end["data"]["reason"], "docked")
        units = end["data"]["units"]
        self.assertEqual([(u["id"], u["kind"]) for u in units], [("NL7", "ca_loc")])
        self.assertAlmostEqual(units[0]["fresh"], 55.5 - self.decay, places=9)  # 1 tick hao trước bến
        self.assertEqual(end["data"]["inventory"], {"items": {"ca_loc": 1}})

    def test_gia_tri_scenario_dang_doi_tuong_duoc_nhan(self):
        with Workdir() as w:
            path = write_json(w.path("sc.json"), {"gather": {"hold": [{"id": "NL9", "kind": "keo_neo", "fresh": 12}]}})
            sc = load_scenario(path, "gather", self.tuning)
            self.assertEqual(sc["hold"][0]["id"], "NL9")

    def test_scenario_tu_choi_fresh_sai_va_id_trung(self):
        with Workdir() as w:
            bad = [
                {"gather": {"hold": [{"id": "NL1", "kind": "ca_loc", "fresh": 101}]}},
                {"gather": {"hold": [{"id": "NL1", "kind": "ca_loc", "fresh": -1}]}},
                {"gather": {"hold": [{"id": "NL1", "kind": "ca_loc"}]}},
                {"gather": {"hold": [{"id": "NL1", "kind": "ca_loc", "fresh": 50},
                                     {"id": "NL1", "kind": "ca_linh", "fresh": 50}]}},
            ]
            for i, body in enumerate(bad):
                path = write_json(w.path(f"bad{i}.json"), body)
                with self.assertRaises(BadInput, msg=str(body)):
                    load_scenario(path, "gather", self.tuning)


if __name__ == "__main__":
    unittest.main()
