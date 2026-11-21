"""Test hộp đen buổi sáng (gather) theo PRD-0 mục F "Gather", E (sự kiện), G (kho).

Mỗi test ghi mã AC-P1-xx (xem docs/verification/phase-1.md). Lát 1–2 đã merge nên mọi test chạy thật.
Quy ước: bước k ghi event ở tick k+1; chạy every=1 để có snapshot mọi tick.
"""

import unittest

from helpers import events
from qa_helpers import press, run_case, snap_at
from legacy_v11 import setUpModule, tearDownModule  # noqa: F401  v1.2: fixture kho đếm chạy trên manifest v1.1 tạm, xem tests/legacy_v11.py

UNDER = [20, 10]   # dưới nước, xa bến
SURF = [20, 0]     # mặt nước, xa bến (bến ở [2,0] bán kính 3)


def sc(**kw) -> dict:
    """Scenario gather cô lập: không nút, không cá, rồi ghi đè bằng kw."""
    base = {"nodes": [], "fish": [], "random_fish": False}
    base.update(kw)
    return base


class Oxygen(unittest.TestCase):
    def test_ac_p1_01_duoi_nuoc_tru_1_moi_tick(self):
        rows, _ = run_case(self, "gather", scenario=sc(player={"pos": UNDER, "oxygen_ticks": 100}), ticks=10)
        self.assertEqual(snap_at(rows, 10)["player"]["oxygen_ticks"], 90)
        self.assertFalse(snap_at(rows, 10)["player"]["at_surface"])

    def test_ac_p1_01_mat_nuoc_hoi_6_moi_tick_va_kep_tran(self):
        rows, _ = run_case(self, "gather", scenario=sc(player={"pos": SURF, "oxygen_ticks": 100}), ticks=10)
        self.assertEqual(snap_at(rows, 10)["player"]["oxygen_ticks"], 160)
        rows, _ = run_case(self, "gather", scenario=sc(player={"pos": SURF, "oxygen_ticks": 1797}), ticks=1)
        self.assertEqual(snap_at(rows, 1)["player"]["oxygen_ticks"], 1800)

    def test_ac_p1_02_dive_mot_lan_khi_qua_mat_nuoc(self):
        rows, _ = run_case(self, "gather", scenario=sc(player={"pos": SURF}),
                           inputs=[{"tick": 0, "move": [0, 1]}], ticks=40)
        dives = events(rows, "dive")
        self.assertEqual(len(dives), 1)
        self.assertGreater(dives[0]["data"]["pos"][1], 0.5)
        self.assertTrue(snap_at(rows, dives[0]["tick"] - 1)["player"]["at_surface"])
        self.assertEqual(events(rows, "surface"), [])

    def test_ac_p1_02_surface_mot_lan_khi_noi_len(self):
        rows, _ = run_case(self, "gather", scenario=sc(player={"pos": [20, 2]}),
                           inputs=[{"tick": 0, "move": [0, -1]}], ticks=60)
        ups = events(rows, "surface")
        self.assertEqual(len(ups), 1)
        self.assertLessEqual(ups[0]["data"]["pos"][1], 0.5)

    def test_ac_p1_03_oxygen_empty_roi_choke_o_t_cong_59(self):
        rows, _ = run_case(self, "gather", scenario=sc(player={"pos": UNDER, "oxygen_ticks": 5}), ticks=70)
        empty = events(rows, "oxygen_empty")
        self.assertEqual([(e["tick"], e["data"]) for e in empty], [(5, {"oxygen_ticks": 0})])
        self.assertEqual(snap_at(rows, 5)["player"]["zero_oxy_ticks"], 1)
        chokes = events(rows, "choke")
        self.assertEqual([(e["tick"], e["data"]) for e in chokes], [(64, {"hp": 2})])
        self.assertEqual(snap_at(rows, 64)["player"]["hp"], 2)
        self.assertEqual(snap_at(rows, 64)["player"]["zero_oxy_ticks"], 0)

    def test_ac_p1_04_ngat_bo_gio_lifo_va_kho_rong(self):
        hold = ["ca_loc", "bong_sung", "ca_linh"]
        player = {"pos": UNDER, "oxygen_ticks": 0, "hp": 1, "zero_oxy_ticks": 59}
        rows, kho = run_case(self, "gather", scenario=sc(player=player, hold=hold), ticks=10, inventory_out=True)
        names = [e["name"] for e in events(rows) if e["tick"] == 1]
        self.assertEqual(names, ["choke", "faint", "gather_end"])
        self.assertEqual(events(rows, "choke")[0]["data"], {"hp": 0})
        self.assertEqual(events(rows, "faint")[0]["data"],
                         {"cause": "choke", "lost": ["ca_linh", "bong_sung", "ca_loc"], "hp": 0})
        self.assertEqual(events(rows, "gather_end")[0]["data"], {"reason": "fainted", "inventory": {"items": {}}})
        self.assertEqual(rows[-1]["reason"], "fainted")
        self.assertEqual(rows[-1]["ticks"], 1, "ngất phải dừng lượt ngay")
        self.assertEqual(kho, {"items": {}})

    def test_ac_p1_05_noi_len_dung_buoc_ngat_thi_khong_ngat(self):
        player = {"pos": [20, 0.55], "vel": [0, -4], "oxygen_ticks": 0, "zero_oxy_ticks": 59}
        rows, _ = run_case(self, "gather", scenario=sc(player=player),
                           inputs=[{"tick": 0, "move": [0, -1]}], ticks=1)
        self.assertEqual(events(rows, "choke"), [])
        self.assertEqual(len(events(rows, "surface")), 1)
        p = snap_at(rows, 1)["player"]
        self.assertEqual((p["hp"], p["oxygen_ticks"], p["zero_oxy_ticks"]), (3, 6, 0))


class Gathering(unittest.TestCase):
    def test_ac_p1_06_hai_nut_dung_mep_hoa_theo_id(self):
        nodes = [{"id": "N2", "kind": "bong_sung", "pos": [18, 0]},
                 {"id": "N1", "kind": "bong_dien_dien", "pos": [22, 0]}]
        rows, _ = run_case(self, "gather", scenario=sc(player={"pos": SURF}, nodes=nodes, hold=["ca_loc"]),
                           inputs=press(0, "interact"), ticks=2)
        g = events(rows, "gather")
        self.assertEqual([(e["tick"], e["data"]) for e in g],
                         [(1, {"node_id": "N1", "kind": "bong_dien_dien", "amount": 1})])
        s = snap_at(rows, 1)
        self.assertEqual(s["hold"], ["ca_loc", "bong_dien_dien"])
        n1 = next(n for n in s["nodes"] if n["id"] == "N1")
        self.assertEqual((n1["ready"], n1["regrow_ticks"]), (False, 1200))

    def test_ac_p1_06_chon_nut_gan_nhat(self):
        nodes = [{"id": "N1", "kind": "bong_dien_dien", "pos": [22, 0]},
                 {"id": "N2", "kind": "bong_sung", "pos": [21, 0]}]
        rows, _ = run_case(self, "gather", scenario=sc(player={"pos": SURF}, nodes=nodes),
                           inputs=press(0, "interact"), ticks=2)
        self.assertEqual([e["data"]["node_id"] for e in events(rows, "gather")], ["N2"])

    def test_ac_p1_06_node_regrown_sau_regrow_s(self):
        nodes = [{"id": "N1", "kind": "bong_sung", "pos": [21, 0]}]
        rows, _ = run_case(self, "gather", scenario=sc(player={"pos": SURF}, nodes=nodes),
                           inputs=press(0, "interact"), ticks=1201, every=100)
        regrown = events(rows, "node_regrown")
        self.assertEqual([(e["tick"], e["data"]) for e in regrown], [(1201, {"node_id": "N1"})])

    def test_ac_p1_07_khong_hai_duoi_nuoc_ngoai_tam_hoac_chua_ready(self):
        nodes = [{"id": "N1", "kind": "bong_sung", "pos": [22, 0]}]
        for player in ({"pos": [22, 1]}, {"pos": [19.9, 0]}):  # dưới nước; ngoài bán kính 2.0
            rows, _ = run_case(self, "gather", scenario=sc(player=player, nodes=nodes),
                               inputs=press(0, "interact"), ticks=2)
            self.assertEqual(events(rows), [], player)
        nodes = [{"id": "N1", "kind": "bong_sung", "pos": [21, 0], "regrow_ticks": 100},
                 {"id": "N2", "kind": "bong_dien_dien", "pos": [22, 0]}]
        rows, _ = run_case(self, "gather", scenario=sc(player={"pos": SURF}, nodes=nodes),
                           inputs=press(0, "interact"), ticks=2)
        self.assertEqual([e["data"]["node_id"] for e in events(rows, "gather")], ["N2"])

    def test_ac_p1_08_hai_khi_gio_day_phat_hold_full(self):
        nodes = [{"id": "N1", "kind": "bong_sung", "pos": [21, 0]}]
        rows, _ = run_case(self, "gather", scenario=sc(player={"pos": SURF}, nodes=nodes, hold=["ca_loc"] * 12),
                           inputs=press(0, "interact"), ticks=2)
        self.assertEqual([e["data"] for e in events(rows, "hold_full")],
                         [{"action": "gather", "node_id": "N1", "required": 1, "free": 0}])
        self.assertEqual(events(rows, "gather"), [])
        self.assertTrue(snap_at(rows, 1)["nodes"][0]["ready"])


class Catching(unittest.TestCase):
    FISH = [{"id": "F2", "kind": "ca_loc", "pos": [32, 10]},
            {"id": "F1", "kind": "ca_linh", "pos": [31, 10]}]

    def test_ac_p1_09_bat_dan_gan_nhat_va_hoi_chieu(self):
        rows, _ = run_case(self, "gather", scenario=sc(player={"pos": [30, 10]}, fish=self.FISH),
                           inputs=press(0, "catch"), ticks=2)
        self.assertEqual([(e["tick"], e["data"]) for e in events(rows, "fish_caught")],
                         [(1, {"fish_id": "F1", "kind": "ca_linh", "yield": 3})])
        s = snap_at(rows, 1)
        self.assertEqual(s["hold"], ["ca_linh"] * 3)
        self.assertEqual([f["id"] for f in s["fish"]], ["F2"])
        self.assertEqual(s["player"]["catch_cd_ticks"], 30)

    def test_ac_p1_09_hoi_chieu_dung_tu_t_cong_L(self):
        scen = sc(player={"pos": [30, 10]}, fish=self.FISH)
        rows, _ = run_case(self, "gather", scenario=scen, inputs=press(0, "catch") + press(29, "catch"), ticks=32)
        self.assertEqual(len(events(rows, "fish_caught")), 1, "tick 29 vẫn đang hồi chiêu")
        rows, _ = run_case(self, "gather", scenario=scen, inputs=press(0, "catch") + press(30, "catch"), ticks=32)
        self.assertEqual([(e["tick"], e["data"]["fish_id"]) for e in events(rows, "fish_caught")],
                         [(1, "F1"), (31, "F2")])

    def test_ac_p1_09_hoa_theo_id_F2_truoc_F10(self):
        fish = [{"id": "F10", "kind": "ca_loc", "pos": [31, 10]}, {"id": "F2", "kind": "ca_loc", "pos": [29, 10]}]
        rows, _ = run_case(self, "gather", scenario=sc(player={"pos": [30, 10]}, fish=fish),
                           inputs=press(0, "catch"), ticks=2)
        self.assertEqual([e["data"]["fish_id"] for e in events(rows, "fish_caught")], ["F2"])

    def test_ac_p1_10_khong_bat_o_mat_nuoc_hoac_ngoai_tam(self):
        cases = [({"pos": [31, 0]}, [{"id": "F1", "kind": "ca_loc", "pos": [31, 1.5]}]),
                 ({"pos": [30, 10]}, [{"id": "F1", "kind": "ca_loc", "pos": [35, 10]}])]
        for player, fish in cases:
            rows, _ = run_case(self, "gather", scenario=sc(player=player, fish=fish), inputs=press(0, "catch"), ticks=2)
            self.assertEqual(events(rows), [], player)
            self.assertEqual(snap_at(rows, 1)["player"]["catch_cd_ticks"], 0)

    def test_ac_p1_10_gio_thieu_cho_hold_full_giu_dan_khong_thu_dan_khac(self):
        rows, _ = run_case(self, "gather", scenario=sc(player={"pos": [30, 10]}, fish=self.FISH, hold=["ca_loc"] * 10),
                           inputs=press(0, "catch"), ticks=2)
        self.assertEqual([e["data"] for e in events(rows, "hold_full")],
                         [{"action": "catch", "fish_id": "F1", "required": 3, "free": 2}])
        self.assertEqual(events(rows, "fish_caught"), [])
        s = snap_at(rows, 1)
        self.assertEqual([f["id"] for f in s["fish"]], ["F1", "F2"])
        self.assertEqual(s["player"]["catch_cd_ticks"], 0)


class DockAndInventory(unittest.TestCase):
    def test_ac_p1_11_cap_ben_xet_truoc_hai(self):
        nodes = [{"id": "N1", "kind": "bong_sung", "pos": [5, 0]}]
        rows, kho = run_case(self, "gather", scenario=sc(player={"pos": [4, 0]}, nodes=nodes, hold=["bong_sung"]),
                             inputs=press(0, "interact"), ticks=5, inventory_out=True)
        self.assertEqual(events(rows, "gather"), [])
        end = events(rows, "gather_end")
        self.assertEqual([e["data"] for e in end], [{"reason": "docked", "inventory": {"items": {"bong_sung": 1}}}])
        self.assertEqual(kho, end[0]["data"]["inventory"])

    def test_ac_p1_11_cap_ben_dung_mep_ban_kinh(self):
        rows, _ = run_case(self, "gather", scenario=sc(player={"pos": [5, 0]}), inputs=press(0, "interact"), ticks=2)
        self.assertEqual(rows[-1]["reason"], "docked")

    def test_ac_p1_12_hai_hop_le_o_buoc_cuoi_van_vao_kho(self):
        nodes = [{"id": "N1", "kind": "bong_sung", "pos": [21, 0]}]
        rows, kho = run_case(self, "gather", scenario=sc(player={"pos": SURF}, nodes=nodes, time_left_ticks=1),
                             inputs=press(0, "interact"), ticks=5, inventory_out=True)
        self.assertEqual([e["name"] for e in events(rows)], ["gather", "gather_end"])
        self.assertEqual(rows[-1]["reason"], "time")
        self.assertEqual(kho, {"items": {"bong_sung": 1}})


if __name__ == "__main__":
    unittest.main()
