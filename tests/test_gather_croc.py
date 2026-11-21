"""Phase 3, P3-01 (cá sấu): tấn công làm rơi cá thể trong giỏ theo LIFO, hồi chiêu, điều kiện dưới nước."""

import unittest

import copy

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import InputPlayer
from chonoi.runner import Session
from chonoi.scenario import load_scenario

from helpers import Workdir, write_json

TICK = 60.0


class GatherCroc(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.g = self.tuning["gather"]
        # tốc độ 0 để cá sấu đứng yên khi kiểm tra tầm và hồi chiêu; test di chuyển tự đặt lại
        self.still = copy.deepcopy(self.tuning)
        self.still["gather"]["croc_speed"] = 0.0

    def session(self, block, seed=1):
        fixture = {"nodes": [], "fish": [], **block}
        return Session("gather", self.still, fixture, seed)

    def run_ticks(self, s, n):
        rows = []
        for _ in range(n):
            rows.extend(s.step(InputPlayer([]).advance(s.tick)))
        return rows

    @staticmethod
    def units(*ids):
        return [{"id": i, "kind": "ca_loc", "fresh": 100.0} for i in ids]

    def test_mac_dinh_co_ca_sau_khi_khong_khai_dan_ca(self):
        s = Session("gather", self.tuning, {}, 1)
        self.assertEqual([c["id"] for c in s.sim.snapshot()["crocs"]], ["C1"])

    def test_khai_dan_ca_thi_khong_co_ca_sau_mac_dinh(self):
        s = self.session({})
        self.assertEqual(s.sim.snapshot()["crocs"], [])

    def test_tan_cong_lam_roi_dung_so_luong_theo_lifo(self):
        s = self.session({"player": {"pos": [50, 10]}, "hold": self.units("NL1", "NL2", "NL3"),
                          "crocs": [{"id": "C1", "pos": [50, 11], "heading_deg": 90}]})
        rows = self.run_ticks(s, 1)
        attack = [r for r in rows if r["name"] == "croc_attack"]
        self.assertEqual(len(attack), 1)
        self.assertEqual(attack[0]["data"]["dropped"], self.g["croc_drop_count"])
        dropped = [r for r in rows if r["name"] == "dropped"][0]["data"]["units"]
        self.assertEqual([u["id"] for u in dropped], ["NL3", "NL2"])
        self.assertEqual([u["id"] for u in s.sim.hold], ["NL1"])

    def test_hoi_chieu_sau_tan_cong(self):
        s = self.session({"player": {"pos": [50, 10]}, "hold": self.units("NL1", "NL2", "NL3", "NL4"),
                          "crocs": [{"id": "C1", "pos": [50, 11], "heading_deg": 90}]})
        self.assertEqual(len([r for r in self.run_ticks(s, 1) if r["name"] == "croc_attack"]), 1)
        cooldown = int(round(self.g["croc_attack_cooldown_s"] * TICK))
        # hồi chiêu đặt cd = cooldown tick ở lần tấn công; tick thứ `cooldown` sau đó mới hết hồi
        self.assertEqual([r for r in self.run_ticks(s, cooldown - 1) if r["name"] == "croc_attack"], [])
        self.assertEqual(len([r for r in self.run_ticks(s, 1) if r["name"] == "croc_attack"]), 1)

    def test_khong_tan_cong_khi_o_mat_nuoc(self):
        s = self.session({"player": {"pos": [50, 0]}, "hold": self.units("NL1"),
                          "crocs": [{"id": "C1", "pos": [50, 1], "heading_deg": 90}]})
        self.assertEqual([r for r in self.run_ticks(s, 1) if r["name"] == "croc_attack"], [])
        self.assertEqual(len(s.sim.hold), 1)

    def test_khong_tan_cong_ngoai_tam(self):
        s = self.session({"player": {"pos": [50, 10]}, "hold": self.units("NL1"),
                          "crocs": [{"id": "C1", "pos": [60, 10], "heading_deg": 90}]})
        self.assertEqual([r for r in self.run_ticks(s, 1) if r["name"] == "croc_attack"], [])

    def test_hang_rong_van_tan_cong_nhung_khong_rot_gi(self):
        s = self.session({"player": {"pos": [50, 10]}, "hold": [],
                          "crocs": [{"id": "C1", "pos": [50, 11], "heading_deg": 90}]})
        rows = self.run_ticks(s, 1)
        attack = [r for r in rows if r["name"] == "croc_attack"]
        self.assertEqual(attack[0]["data"]["dropped"], 0)
        self.assertEqual([r for r in rows if r["name"] == "dropped"], [])

    def test_hoa_khoang_cach_chon_ca_sau_co_id_nho_hon(self):
        s = self.session({"player": {"pos": [50, 10]}, "hold": self.units("NL1", "NL2", "NL3"),
                          "crocs": [{"id": "C10", "pos": [50, 11], "heading_deg": 90},
                                    {"id": "C2", "pos": [50, 9], "heading_deg": 90}]})
        rows = self.run_ticks(s, 1)
        self.assertEqual([r for r in rows if r["name"] == "croc_attack"][0]["data"]["croc_id"], "C2")

    def test_ca_sau_boi_1_met_moi_giay(self):
        s = Session("gather", self.tuning,
                    {"nodes": [], "fish": [], "crocs": [{"id": "C1", "pos": [30, 10], "heading_deg": 0}]}, 1)
        self.run_ticks(s, 60)
        self.assertAlmostEqual(s.sim.crocs[0]["pos"][0], 30 + self.g["croc_speed"], places=6)

    def test_scenario_tu_choi_ca_sau_tren_mat_nuoc(self):
        with Workdir() as w:
            path = write_json(w.path("sc.json"), {"gather": {"crocs": [{"id": "C1", "pos": [30, 0]}]}})
            with self.assertRaises(BadInput):
                load_scenario(path, "gather", self.tuning)


if __name__ == "__main__":
    unittest.main()
