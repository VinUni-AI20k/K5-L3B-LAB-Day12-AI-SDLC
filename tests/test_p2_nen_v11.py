"""Test nền Test Contract v1.1 (Integrator): manifest, CLI, inputs, pause, scenario, đàn cá đầu ca, quái theo Ngày,
nâng cấp. Ticket-02 mục 1, 2, 4.1-4.5. Phần luật của từng lát (Cá Sấu, cá bơi, day, Shop) có test riêng.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_p2_nen_v11 -v
"""

import unittest

from chonoi.contract import load_contract, plan_ingredients
from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim
from chonoi.sim.quan import QuanSim
from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

CONTRACT = load_contract()
T = CONTRACT["tuning"]
G = T["gather"]


def headless(w, *args, scenario=None, inputs=None):
    extra = []
    if scenario is not None:
        extra += ["--scenario", write_json(w.path("sc.json"), scenario)]
    if inputs is not None:
        extra += ["--inputs", write_json(w.path("in.json"), inputs)]
    return run_headless(*args, *extra, "--out", w.path("o.jsonl"))


class Manifest(unittest.TestCase):
    def test_v11_so_chuan(self):
        self.assertEqual(CONTRACT["contract_version"], "1.1")
        self.assertEqual(len(T["menu"]), 6)
        self.assertEqual([s["id"] for s in T["quan"]["stoves"]], ["B1", "B2"])
        self.assertEqual([t["id"] for t in T["quan"]["tables"]], ["T1", "T2", "T3", "T4"])
        self.assertEqual(G["fish_initial"], 8)
        self.assertEqual(G["fish_yield"], {"ca_linh": 3, "ca_loc": 1, "ca_keo": 2})
        self.assertEqual({n["id"]: n["kind"] for n in G["nodes"]}["N6"], "keo_neo")
        self.assertEqual(T["menu"]["lau_mam"]["price"], 200)

    def test_day_plan_ingredients_bang_tong_cong_thuc(self):
        self.assertEqual([p["day"] for p in T["day_plan"]], [1, 2, 3, 4, 5])
        for p in T["day_plan"]:
            self.assertEqual(p["ingredients"], plan_ingredients(T["menu"], p["dishes"]), p["day"])
        self.assertEqual(T["day_plan"][0]["ingredients"], {"ca_loc": 3, "bong_sung": 6})

    def test_shop_upgrades(self):
        ups = T["shop"]["upgrades"]
        self.assertEqual([(u["price"], u["oxygen_max_s"]) for u in ups["oxygen"]], [(200, 45), (400, 60)])
        self.assertEqual([(u["price"], u["hp_max"]) for u in ups["hp"]], [(250, 4), (500, 5)])
        self.assertEqual(T["shop"]["max_ticks"], 600)


class Cli(unittest.TestCase):
    def test_days_chi_dung_voi_day_va_trong_1_5(self):
        with Workdir() as w:
            self.assertEqual(headless(w, "--mode", "gather", "--seed", "1", "--ticks", "0", "--days", "1")[0], 2)
            for bad in ("0", "6", "x"):
                self.assertEqual(headless(w, "--mode", "day", "--seed", "1", "--ticks", "0", "--days", bad)[0], 2, bad)

    def test_buy_va_shop_done_hop_le_nhung_bo_qua_ngoai_shop(self):
        with Workdir() as w:
            code, err = headless(w, "--mode", "gather", "--seed", "1", "--ticks", "5",
                                 inputs=frames({"tick": 0, "buy": "oxygen", "shop_done": True}))
            self.assertEqual(code, 0, err)
            self.assertEqual(events(read_jsonl(w.path("o.jsonl"))), [])

    def test_buy_sai_kieu_ma_2(self):
        with Workdir() as w:
            for bad in ("", 5, True):
                code, _ = headless(w, "--mode", "gather", "--seed", "1", "--ticks", "5",
                                   inputs=frames({"tick": 0, "buy": bad}))
                self.assertEqual(code, 2, repr(bad))

    def test_kho_6_nguyen_lieu(self):
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": {"ca_keo": 2, "keo_neo": 1}})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", inv,
                                     "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"], {"ca_keo": 2, "keo_neo": 1})


class Pause(unittest.TestCase):
    def run_pause(self, extra_frames=(), ticks=20, block=None):
        with Workdir() as w:
            sc = {"gather": block or {"player": {"pos": [50, 10]}, "random_fish": False}}
            fr = [{"tick": 0, "pause": True}, {"tick": 1, "pause": False}, *extra_frames,
                  {"tick": 9, "pause": True}, {"tick": 10, "pause": False}]
            fr.sort(key=lambda f: f["tick"])
            code, err = headless(w, "--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--snapshot-every", "1",
                                 scenario=sc, inputs={"frames": fr})
            self.assertEqual(code, 0, err)
            return read_jsonl(w.path("o.jsonl"))

    def test_pause_dung_dong_ho_va_resume_chay_ngay(self):
        rows = self.run_pause()
        self.assertEqual([(e["name"], e["tick"]) for e in events(rows)], [("paused", 1), ("resumed", 10)])
        s = {r["tick"]: r for r in snapshots(rows)}
        self.assertEqual(s[5]["state"], "paused")
        self.assertEqual((s[5]["sim_tick"], s[5]["time_left_ticks"]), (0, s[0]["time_left_ticks"]))
        self.assertEqual(s[5]["player"]["oxygen_ticks"], s[0]["player"]["oxygen_ticks"])
        # bước resume (tick 10) chạy gameplay ngay
        self.assertEqual((s[10]["state"], s[10]["sim_tick"]), ("playing", 1))
        self.assertEqual(s[20]["sim_tick"], 11)
        self.assertEqual(rows[-1]["sim_tick"], 11)
        self.assertEqual(rows[-1]["ticks"], 20)

    def test_trong_pause_bo_qua_canh_hanh_dong(self):
        rows = self.run_pause(extra_frames=[{"tick": 3, "interact": True}, {"tick": 4, "interact": False}],
                              block={"player": {"pos": [2, 0]}, "random_fish": False, "hold": ["ca_loc"]})
        self.assertEqual(events(rows, "gather_end"), [])
        self.assertEqual(rows[-1]["reason"], "tick_limit")


class GatherV11(unittest.TestCase):
    def sim(self, scenario=None, seed=1, day=1, ups=None):
        return GatherSim(T, scenario or {}, Streams(seed), IdAllocator(), day=day, active_upgrades=ups)

    # 8 đàn đầu ca, cá bơi, cá sinh là lát của B: test nằm trong file test của B.

    def test_random_fish_false_khong_co_ca(self):
        self.assertEqual(self.sim({"random_fish": False}).fish, [])

    def test_fish_fixture_thay_dan_ban_dau(self):
        s = self.sim({"fish": [{"id": "F9", "kind": "ca_keo", "pos": [30, 24], "age_ticks": 5}]})
        self.assertEqual([(f["id"], f["age_ticks"]) for f in s.fish], [("F9", 5)])

    def test_quai_theo_ngay(self):
        # Cá Sấu: M1 từ Ngày 1, M2 từ Ngày 3. M3 (Rắn Hổ Mây) chỉ có khi bật mở rộng snake.
        snake = ["M3"] if "snake" in CONTRACT.get("extensions", []) else []
        self.assertEqual([m["id"] for m in self.sim(day=1).monsters], ["M1"] + snake)
        self.assertEqual([m["id"] for m in self.sim(day=3).monsters], ["M1", "M2"] + snake)
        m1 = self.sim().monsters[0]
        self.assertEqual((m1["state"], m1["target_idx"], m1["pos"], m1["recoil_dir"]), ("patrol", 1, [60.0, 24.0], None))

    def test_nang_cap_oxy_va_mau(self):
        s = self.sim(ups={"oxygen": 1, "hp": 2})
        self.assertEqual((s.oxygen_max, s.oxygen_ticks, s.hp_max, s.hp), (2700, 2700, 5, 5))
        s = self.sim(ups={"oxygen": 2})
        self.assertEqual(s.oxygen_max, 3600)
        s = self.sim()
        self.assertEqual((s.oxygen_max, s.hp_max), (1800, 3))

    def test_snapshot_co_monsters(self):
        with Workdir() as w:
            code, err = headless(w, "--mode", "gather", "--seed", "1", "--ticks", "0",
                                 scenario={"gather": {"fish": [{"id": "F1", "kind": "ca_keo", "pos": [30, 24]}]}})
            self.assertEqual(code, 0, err)
            s = snapshots(read_jsonl(w.path("o.jsonl")))[0]
            snake = ["M3"] if "snake" in CONTRACT.get("extensions", []) else []
            self.assertEqual([m["id"] for m in s["monsters"]], ["M1"] + snake)
            self.assertEqual(s["player"]["hp_max"], 3)
            self.assertEqual(s["fish"][0]["age_ticks"], 0)


class ScenarioV11(unittest.TestCase):
    def code(self, mode, sc):
        with Workdir() as w:
            return headless(w, "--mode", mode, "--seed", "1", "--ticks", "0", scenario=sc)[0]

    def test_loai_moi_hop_le(self):
        self.assertEqual(self.code("gather", {"gather": {
            "nodes": [{"id": "N1", "kind": "keo_neo", "pos": [76, 0]}],
            "fish": [{"id": "F1", "kind": "ca_keo", "pos": [30, 24]}],
            "hold": ["ca_keo", "keo_neo"]}}), 0)

    def test_monsters_fixture(self):
        ok = {"id": "M1", "kind": "ca_sau", "pos": [50, 20], "waypoints": [[50, 20], [54, 20]]}
        self.assertEqual(self.code("gather", {"gather": {"monsters": [ok]}}), 0)
        rec = dict(ok, state="recoil", state_ticks_left=10, recoil_dir=[1, 0])
        self.assertEqual(self.code("gather", {"gather": {"monsters": [rec]}}), 0)
        for bad in (dict(ok, pos=[50, 5]),                          # ngoài dải độ sâu loài [10, 30]
                    dict(ok, kind="ca_map"),                        # loài lạ
                    dict(ok, waypoints=[[50, 20]]),                 # thiếu waypoint
                    dict(ok, target_idx=2),
                    dict(ok, state="recoil", state_ticks_left=0, recoil_dir=[1, 0]),
                    dict(ok, state="recoil", state_ticks_left=5),   # thiếu recoil_dir
                    dict(ok, recoil_dir=[1, 0]),                    # recoil_dir khi patrol
                    dict(ok, speed=3)):                             # trường lạ
            self.assertEqual(self.code("gather", {"gather": {"monsters": [bad]}}), 2, bad)

    def test_fish_truong_la_ma_2(self):
        self.assertEqual(self.code("gather", {"gather": {"fish": [{"id": "F1", "kind": "ca_loc", "pos": [30, 10],
                                                                    "speed": 1}]}}), 2)


class QuanCarry(unittest.TestCase):
    def test_carry_va_plan_dishes(self):
        q = QuanSim(T, {}, Streams(1), IdAllocator(), inventory={},
                    plan_dishes=["goi_bong_sung", "ca_loc_nuong_trui"],
                    carry={"money": 150, "earned": 300, "reputation": 3.4})
        self.assertEqual((q.money, q.earned, q.reputation, q.shift_earned), (150, 300, 3.4, 0))
        self.assertEqual(q.plan_dishes, ["ca_loc_nuong_trui", "goi_bong_sung"])
        q = QuanSim(T, {}, Streams(1), IdAllocator())
        self.assertEqual((q.money, q.earned, q.reputation, q.plan_dishes), (0, 0, 3.0, None))


if __name__ == "__main__":
    unittest.main()
