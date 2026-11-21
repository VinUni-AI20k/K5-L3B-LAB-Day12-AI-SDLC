"""Lát 0 (Phase 2): nền Test Contract v1.1 — số chuẩn, khóa mới, kind mới, scenario mới, inputs mới.

Đối chiếu docs/prd/phase-2.md mục 1, 2, 4.1–4.4. Phần hành vi (cá bơi/sinh theo lịch, Cá Sấu di chuyển, day, Shop)
thuộc lát 1, 2, 5; ở đây chỉ kiểm cấu hình, đàn đầu ca, snapshot và kiểm đầu vào.
"""

import json
import math
import unittest

from chonoi.contract import load_contract, plan_ingredients
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import LiveInputs
from chonoi.rng import Streams
from chonoi.scenario import load_scenario
from chonoi.sim.gather import GatherSim
from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json

TUNING = load_contract()["tuning"]
G = TUNING["gather"]


def gather_rows(w, block=None, seed=1, ticks=0, out="o.jsonl"):
    args = ["--mode", "gather", "--seed", str(seed), "--ticks", str(ticks), "--out", w.path(out)]
    if block is not None:
        args += ["--scenario", write_json(w.path("sc.json"), {"gather": block})]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path(out))


class ContractV11(unittest.TestCase):
    def test_so_chuan_v11(self):
        with open("game.contract.json", encoding="utf-8") as f:
            self.assertEqual(json.load(f)["contract_version"], "1.1")
        self.assertEqual(G["fish_initial"], 8)
        self.assertEqual(G["fish_yield"], {"ca_linh": 3, "ca_loc": 1, "ca_keo": 2})
        self.assertEqual([n["id"] for n in G["nodes"]], ["N1", "N2", "N3", "N4", "N5", "N6"])
        self.assertEqual([s["id"] for s in TUNING["quan"]["stoves"]], ["B1", "B2"])
        self.assertEqual([t["id"] for t in TUNING["quan"]["tables"]], ["T1", "T2", "T3", "T4"])
        self.assertEqual(len(TUNING["menu"]), 6)
        sp = G["monsters"]["spawns"]
        self.assertEqual([(m["id"], m["from_day"]) for m in sp], [("M1", 1), ("M2", 3)])

    def test_day_plan_ingredients_bang_tong_cong_thuc(self):
        cells = []
        for e in TUNING["day_plan"]:
            self.assertEqual(e["ingredients"], plan_ingredients(e["dishes"], TUNING["menu"]), e["day"])
            cells.append(sum(e["ingredients"].values()))
        self.assertEqual(cells, [9, 10, 12, 9, 10])  # cột "Số ô cần" của Ticket-02

    def test_upgrades_ap_dung_oxygen_hp(self):
        sim = GatherSim(TUNING, {"random_fish": False}, Streams(1), IdAllocator(), upgrades={"oxygen": 2, "hp": 1})
        self.assertEqual((sim.oxygen_max, sim.oxygen_ticks, sim.hp, sim.hp_max), (3600, 3600, 4, 4))
        base = GatherSim(TUNING, {"random_fish": False}, Streams(1), IdAllocator())
        self.assertEqual((base.oxygen_max, base.hp_max), (1800, 3))


class InitialFish(unittest.TestCase):
    def test_tam_dan_dau_ca_o_diem_sinh_khac_nhau(self):
        with Workdir() as w:
            fish = snapshots(gather_rows(w))[0]["fish"]
        self.assertEqual([f["id"] for f in fish], [f"F{i}" for i in range(1, 9)])
        pts = [tuple(f["pos"]) for f in fish]
        for f in fish:
            self.assertIn(f["pos"][0], G["fish_spawn_x"])
            self.assertIn(f["pos"][1], G["fish_spawn_depths"][f["kind"]])
            self.assertEqual(f["age_ticks"], 0)
        for i, a in enumerate(pts):
            for b in pts[i + 1:]:
                self.assertGreater(math.dist(a, b), G["fish_spawn_clearance"])

    def test_cung_seed_giong_khac_seed_co_the_khac(self):
        with Workdir() as w:
            a = snapshots(gather_rows(w, seed=7, out="a.jsonl"))[0]["fish"]
            b = snapshots(gather_rows(w, seed=7, out="b.jsonl"))[0]["fish"]
            c = [snapshots(gather_rows(w, seed=s, out=f"c{s}.jsonl"))[0]["fish"] for s in range(1, 6)]
        self.assertEqual(a, b)
        self.assertTrue(any(x != c[0] for x in c[1:]), "seed khác nhau phải cho bố trí khác nhau")

    def test_random_fish_false_va_fixture_thay_dan_ban_dau(self):
        with Workdir() as w:
            self.assertEqual(snapshots(gather_rows(w, {"random_fish": False}))[0]["fish"], [])
            fx = [{"id": "F3", "kind": "ca_keo", "pos": [50, 25], "age_ticks": 4}]
            fish = snapshots(gather_rows(w, {"fish": fx}))[0]["fish"]
        self.assertEqual(fish, [{"id": "F3", "pos": [50, 25], "kind": "ca_keo", "heading_deg": 0, "age_ticks": 4}])


class Monsters(unittest.TestCase):
    def test_snapshot_ngay_1_chi_co_m1(self):
        with Workdir() as w:
            m = snapshots(gather_rows(w))[0]["monsters"]
        self.assertEqual(m, [{"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]],
                              "target_idx": 1, "state": "patrol", "state_ticks_left": 0, "recoil_dir": None}])

    def test_ngay_3_co_them_m2(self):
        sim = GatherSim(TUNING, {"random_fish": False}, Streams(1), IdAllocator(), day=3)
        self.assertEqual([m["id"] for m in sim.monsters], ["M1", "M2"])

    def test_scenario_monsters_hop_le_va_mau_thuan_ma_2(self):
        ok = {"id": "M9", "kind": "ca_sau", "pos": [30, 20], "waypoints": [[30, 20], [34, 20]],
              "state": "recoil", "state_ticks_left": 10, "recoil_dir": [-1, 0]}
        with Workdir() as w:
            m = snapshots(gather_rows(w, {"monsters": [ok]}))[0]["monsters"]
            self.assertEqual([x["id"] for x in m], ["M9"])
            bads = [dict(ok, state_ticks_left=0), dict(ok, recoil_dir=[1, 1]), dict(ok, pos=[30, 5]),
                    dict(ok, state="patrol"), dict(ok, kind="ran"), dict(ok, target_idx=2),
                    dict(ok, waypoints=[[30, 20]]), dict(ok, speed=1)]
            for bad in bads:
                sc = write_json(w.path("bad.json"), {"gather": {"monsters": [bad]}})
                code, _ = run_headless("--mode", "gather", "--seed", "1", "--ticks", "0", "--scenario", sc,
                                       "--out", w.path("x.jsonl"))
                self.assertEqual(code, 2, bad)


class KindsAndScenario(unittest.TestCase):
    def test_kind_moi_qua_kho_va_gio(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"hold": ["ca_keo", "keo_neo", "ca_keo"]}})
            inp = write_json(w.path("in.json"), {"frames": [{"tick": 0, "interact": True}]})
            inv = w.path("kho.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1", "--scenario", sc, "--inputs", inp,
                                     "--inventory-out", inv, "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"ca_keo": 2, "keo_neo": 1}})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", inv,
                                     "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"], {"ca_keo": 2, "keo_neo": 1})

    def test_fish_age_ticks_va_truong_la(self):
        with Workdir() as w:
            for bad in ({"fish": [{"id": "F1", "kind": "ca_keo", "pos": [50, 25], "age_ticks": -1}]},
                        {"fish": [{"id": "F1", "kind": "ca_keo", "pos": [50, 25], "speed": 2}]},
                        {"fish": [{"id": f"F{i}", "kind": "ca_linh", "pos": [10 + i, 5]} for i in range(13)]}):
                sc = write_json(w.path("bad.json"), {"gather": bad})
                code, _ = run_headless("--mode", "gather", "--seed", "1", "--ticks", "0", "--scenario", sc,
                                       "--out", w.path("x.jsonl"))
                self.assertEqual(code, 2, bad)

    def test_scenario_day(self):
        with Workdir() as w:
            ok = write_json(w.path("d.json"), {"day": {"money": 200, "earned": 200, "upgrades": {"oxygen": 1}},
                                               "gather": {"hold": ["ca_loc"], "random_fish": False}})
            d = load_scenario(ok, "day", TUNING)
            self.assertEqual((d["day"]["money"], d["gather"]["hold"], d["quan"]), (200, ["ca_loc"], {}))
            for bad in ({"quan": {"stock": {"ca_loc": 1}}}, {"quan": {"reputation": 3}},
                        {"day": {"money": 300, "earned": 200}}, {"day": {"money": 5}},
                        {"day": {"upgrades": {"oxygen": 3}}}, {"day": {"lives": 1}},
                        {"day": {"day_plan": [{"day": 1, "dishes": {"pho": 1}}]}},
                        {"day": {"day_plan": [{"day": 1, "dishes": {"goi_bong_sung": 1},
                                               "ingredients": {"bong_sung": 3}}]}}):
                with self.assertRaises(BadInput, msg=bad):
                    load_scenario(write_json(w.path("b.json"), bad), "day", TUNING)
            with self.assertRaises(BadInput):
                load_scenario(write_json(w.path("e.json"), {"day": {}}), "gather", TUNING)

    def test_live_inputs_buy_mot_lan(self):
        li = LiveInputs()
        li.set(buy="hp", pause=True)
        s = li.advance()
        self.assertEqual((s.buy, s.pressed("pause")), ("hp", True))
        self.assertIsNone(li.advance().buy)


if __name__ == "__main__":
    unittest.main()
