"""Phase 2, P2-01: cá bơi, đổi hướng, phản xạ mép, sinh đàn, bắt cá, deterministic."""

import math
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer
from chonoi.runner import Session


class GatherFish(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.g = self.tuning["gather"]

    def session(self, block, seed=1):
        fixture = {"nodes": [], "fish": [], **block}
        return Session("gather", self.tuning, fixture, seed)

    def run_ticks(self, s, n):
        rows = []
        for _ in range(n):
            rows.extend(s.step(InputPlayer([]).advance(s.tick)))
        return rows

    def test_ca_boi_dung_toc_do_1_5_m_moi_giay(self):
        s = self.session({"fish": [{"id": "F1", "kind": "ca_linh", "pos": [30, 10], "heading_deg": 0}]})
        self.run_ticks(s, 60)  # 1 giây
        x, d = s.sim.fish[0]["pos"]
        self.assertAlmostEqual(x, 30 + self.g["fish_speed"], places=6)
        self.assertAlmostEqual(d, 10, places=6)

    def test_doi_huong_sau_dung_120_buoc(self):
        s = self.session({"fish": [{"id": "F1", "kind": "ca_loc", "pos": [30, 10], "heading_deg": 45}]})
        self.run_ticks(s, 119)
        self.assertEqual(s.sim.fish[0]["heading_deg"], 45)
        self.run_ticks(s, 1)
        self.assertNotEqual(s.sim.fish[0]["heading_deg"], 45)
        self.assertEqual(s.sim.fish[0]["age_ticks"], 120)

    def test_doi_huong_theo_seed_va_deterministic(self):
        block = {"fish": [{"id": "F1", "kind": "ca_loc", "pos": [30, 10], "heading_deg": 45}]}
        a = self.session(block, seed=7)
        b = self.session(block, seed=7)
        c = self.session(block, seed=8)
        self.run_ticks(a, 300)
        self.run_ticks(b, 300)
        self.run_ticks(c, 300)
        self.assertEqual(a.sim.fish, b.sim.fish)
        self.assertNotEqual(a.sim.fish[0]["heading_deg"], c.sim.fish[0]["heading_deg"])

    def test_phan_xa_mep_phai(self):
        bx = self.g["fish_x"][1]
        s = self.session({"fish": [{"id": "F1", "kind": "ca_linh", "pos": [bx - 0.01, 10], "heading_deg": 0}]})
        self.run_ticks(s, 1)
        f = s.sim.fish[0]
        self.assertAlmostEqual(f["pos"][0], bx + 0.01 - self.g["fish_speed"] / self.tuning["tick_hz"])
        self.assertAlmostEqual(f["heading_deg"], 180.0, places=6)

    def test_phan_xa_mep_nong_cua_loai(self):
        shallow = self.g["fish_depths"]["ca_linh"][0]
        s = self.session({"fish": [{"id": "F1", "kind": "ca_linh", "pos": [30, shallow + 0.01],
                                    "heading_deg": 270}]})
        self.run_ticks(s, 1)
        f = s.sim.fish[0]
        self.assertAlmostEqual(f["pos"][1], shallow - 0.01 + self.g["fish_speed"] / self.tuning["tick_hz"])
        self.assertAlmostEqual(f["heading_deg"], 90.0, places=6)

    def test_sinh_dan_dung_chu_ky_360_tick(self):
        s = self.session({"fish": []})
        self.run_ticks(s, self.g["fish_spawn_ticks"] - 1)
        self.assertEqual(len(s.sim.fish), 0)
        rows = self.run_ticks(s, 1)
        self.assertEqual(len(s.sim.fish), 1)
        new = s.sim.fish[0]
        self.assertTrue(new["id"].startswith("F"))
        self.assertIn(new["kind"], ("ca_linh", "ca_loc", "ca_keo"))
        self.assertIn(new["pos"][0], self.g["fish_spawn_x"])
        self.assertIn(new["pos"][1], self.g["fish_spawn_depths"][new["kind"]])
        self.assertEqual(new["age_ticks"], 0)
        self.assertEqual([row["name"] for row in rows], ["fish_spawned"])

    def test_random_fish_false_keeps_fixture_still_and_prevents_spawns(self):
        fish = {"id": "F1", "kind": "ca_linh", "pos": [30, 5], "heading_deg": 0, "age_ticks": 119}
        s = self.session({"random_fish": False, "fish": [fish]})
        self.assertEqual(self.run_ticks(s, self.g["fish_spawn_ticks"]), [])
        self.assertEqual(s.sim.fish, [fish])

    def test_tran_12_dan(self):
        fish = [{"id": f"F{i}", "kind": "ca_linh", "pos": [10 + i, 10], "heading_deg": 0} for i in range(1, 13)]
        s = self.session({"fish": fish})
        self.run_ticks(s, self.g["fish_spawn_ticks"] * 2)
        self.assertEqual(len(s.sim.fish), self.g["fish_max"])

    def test_ti_le_sinh_theo_trong_so(self):
        s = self.session({"fish": []}, seed=1)
        counts = {"ca_linh": 0, "ca_loc": 0, "ca_keo": 0}
        n = 3000
        for _ in range(n):
            s.sim.fish = []
            s.sim._spawn_fish()
            counts[s.sim.fish[0]["kind"]] += 1
        for kind, w in self.g["fish_weights"].items():
            self.assertAlmostEqual(counts[kind] / n, w, delta=0.03, msg=kind)

    def test_bat_ca_keo_nhan_dung_yield(self):
        s = self.session({"player": {"pos": [20, 5]},
                          "fish": [{"id": "F2", "kind": "ca_keo", "pos": [21, 5], "heading_deg": 0}]})
        rows = s.step(InputPlayer([{"tick": 0, "catch": True}]).advance(s.tick))
        caught = [r for r in rows if r["name"] == "fish_caught"]
        self.assertEqual(len(caught), 1)
        self.assertEqual(caught[0]["data"]["yield"], self.g["fish_yield"]["ca_keo"])
        self.assertEqual(s.sim.hold, ["ca_keo"] * self.g["fish_yield"]["ca_keo"])

    def test_snapshot_co_du_6_loai_nguyen_lieu(self):
        snap = Session("gather", self.tuning, {}, 1).sim.snapshot()
        node_kinds = {n["kind"] for n in snap["nodes"]}
        fish_kinds = {f["kind"] for f in snap["fish"]}
        self.assertEqual(node_kinds, {"bong_dien_dien", "bong_sung", "keo_neo"})
        self.assertEqual(fish_kinds, {"ca_linh", "ca_loc", "ca_keo"})

    def test_mac_dinh_khoi_tao_8_dan(self):
        s = Session("gather", self.tuning, {}, 1)
        self.assertEqual(len(s.sim.fish), 8)


if __name__ == "__main__":
    unittest.main()
