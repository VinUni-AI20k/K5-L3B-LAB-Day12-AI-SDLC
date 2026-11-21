"""Lát 0 Phase 3: nền Test Contract v1.2 — chonoi/items.py, file kho cá thể, contract freshness, scenario v1.2,
giỏ cá thể + `lost` LIFO (docs/prd/phase-3.md, docs/plan/phase-3.md mục 2).

Manifest chính còn v1.1 tới khi lát 2/3/4 xong (Ticket-03: "bật v1.2 khi cả hai đầu bàn giao đã sẵn sàng").
Test headless ở đây dựng một manifest v1.2 tạm và trỏ CHONOI_CONTRACT tới nó.
"""

import copy
import json
import os
import unittest

from chonoi import items as it
from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inventory import KINDS, read_inventory
from chonoi.rng import Streams
from chonoi.scenario import load_scenario
from chonoi.sim.gather import GatherSim
from helpers import ROOT, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

FRESH = {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}


def manifest_v12():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        m = json.load(f)
    m["contract_version"] = "1.2"
    m["tuning"]["freshness"] = dict(FRESH)
    return m


T12 = manifest_v12()["tuning"]


def item(i, kind="ca_linh", fresh=100):
    return {"id": f"I{i}", "kind": kind, "fresh": fresh}


class V12Headless:
    """Chạy headless với manifest v1.2 tạm."""

    def __enter__(self):
        self.w = Workdir().__enter__()
        self.old = os.environ.get("CHONOI_CONTRACT")
        os.environ["CHONOI_CONTRACT"] = write_json(self.w.path("contract.json"), manifest_v12())
        return self.w

    def __exit__(self, *a):
        if self.old is None:
            os.environ.pop("CHONOI_CONTRACT", None)
        else:
            os.environ["CHONOI_CONTRACT"] = self.old
        self.w.__exit__(*a)


class Items(unittest.TestCase):
    def test_nguong_so_truoc_lam_tron_va_hao_don_vi_nguyen(self):
        self.assertFalse(it.is_spoiled(item(1, fresh=30), T12))
        self.assertTrue(it.is_spoiled(item(1, fresh=29.996), T12))
        x = [item(1, fresh=30)]  # ví dụ ticket: fresh 30 -> ươn ngay bước đầu ở gather
        self.assertEqual([i["id"] for i in it.decay(x, 0.5 / 60, T12)], ["I1"])
        y = [item(1, fresh=30.5)]  # 30.5 -> ươn ở bước 61 (2 đơn vị/bước, 7320 -> < 7200)
        steps = next(k for k in range(1, 200) if it.decay(y, 0.5 / 60, T12))
        self.assertEqual(steps, 61)
        z = [item(1, fresh=100)]
        for _ in range(240):
            it.decay(z, 0.25 / 60, T12)
        self.assertEqual(z[0]["fresh"], 99.0, "quán 0.25/s: 240 bước = 1 điểm, không trôi số")

    def test_decay_tra_vua_uon_theo_id_mot_lan_va_kep_0(self):
        x = [item(10, fresh=30), item(2, fresh=30), item(3, fresh=5)]
        self.assertEqual([i["id"] for i in it.decay(x, 0.5 / 60, T12)], ["I2", "I10"])
        self.assertEqual(it.decay(x, 0.5 / 60, T12), [], "spoiled chỉ một lần")
        low = [item(1, fresh=0.001)]
        it.decay(low, 0.5 / 60, T12)
        self.assertEqual(low[0]["fresh"], 0.0)

    def test_pick_freshest_usable_price(self):
        stock = [item(3, fresh=90), item(1, fresh=95), item(2, fresh=95), item(4, fresh=20), item(5, "ca_loc", 80)]
        self.assertEqual(it.pick_freshest(stock, "ca_linh", 2, set(), T12), ["I1", "I2"], "tươi nhất, hòa id nhỏ")
        self.assertEqual(it.pick_freshest(stock, "ca_linh", 2, {"I1"}, T12), ["I2", "I3"])
        self.assertIsNone(it.pick_freshest(stock, "ca_linh", 4, set(), T12), "hàng ươn không tính")
        self.assertEqual(it.usable_by_kind(stock, {"I3"}, T12), {"ca_linh": 2, "ca_loc": 1})
        self.assertEqual(it.price_by_fresh(60, [item(1, fresh=97.5)]), 58)
        self.assertEqual(it.price_by_fresh(120, [item(1, fresh=100), item(2, fresh=99.75)]), 119)
        self.assertEqual(it.counts([item(2, "ca_loc"), item(1)]), {"ca_linh": 1, "ca_loc": 1})

    def test_new_item_id_noi_tiep_khong_tai_dung(self):
        ids = IdAllocator()
        ids.reserve("I7")
        self.assertEqual(it.new_item(ids, "ca_loc", 100), {"id": "I8", "kind": "ca_loc", "fresh": 100.0})

    def test_schema_file_kho_v12(self):
        obj = {"items": [item(2, "ca_loc", 97.5), item(1)]}
        got = it.from_file(obj, KINDS)
        self.assertEqual(it.to_file(got), {"items": [item(1, fresh=100.0), item(2, "ca_loc", 97.5)]})
        self.assertEqual(it.to_file([]), {"items": []})
        bads = [{"items": {"ca_loc": 1}}, {"items": [item(1), item(1)]}, {"items": [item(1, "ca_la_lung")]},
                {"items": [item(1, fresh=100.5)]}, {"items": [item(1, fresh=-1)]}, {"items": [dict(item(1), x=1)]},
                {"items": [{"id": "", "kind": "ca_loc", "fresh": 1}]}, {"items": [item(1, fresh=True)]},
                {"items": []}, ]
        for bad in bads[:-1]:
            with self.assertRaises(BadInput, msg=bad):
                it.from_file(bad, KINDS)
        self.assertEqual(it.from_file(bads[-1], KINDS), [])


class ContractV12(unittest.TestCase):
    def test_contract_version_va_freshness(self):
        with Workdir() as w:
            load_contract(write_json(w.path("ok.json"), manifest_v12()))
            m = manifest_v12()
            del m["tuning"]["freshness"]
            with self.assertRaises(BadInput):
                load_contract(write_json(w.path("thieu.json"), m))
            m = manifest_v12()
            m["contract_version"] = "1.1"
            with self.assertRaises(BadInput):
                load_contract(write_json(w.path("du.json"), m))
            for key, bad in (("gather_decay_per_s", 0.3), ("spoiled_below", 120), ("initial", -1)):
                m = manifest_v12()
                m["tuning"]["freshness"][key] = bad
                with self.assertRaises(BadInput, msg=key):
                    load_contract(write_json(w.path("b.json"), m))
            m = manifest_v12()
            m["contract_version"] = "2.0"
            with self.assertRaises(BadInput):
                load_contract(write_json(w.path("v.json"), m))

    def test_read_inventory_chon_schema_theo_phien_ban(self):
        with Workdir() as w:
            dem = write_json(w.path("dem.json"), {"items": {"ca_loc": 1}})
            cathe = write_json(w.path("ct.json"), {"items": [item(1, "ca_loc", 97.5)]})
            self.assertEqual(read_inventory(dem), {"ca_loc": 1})
            self.assertEqual(read_inventory(cathe, v12=True), [item(1, "ca_loc", 97.5)])
            with self.assertRaises(BadInput):
                read_inventory(dem, v12=True)
            with self.assertRaises(BadInput):
                read_inventory(cathe)


class ScenarioV12(unittest.TestCase):
    def load(self, w, block, mode):
        return load_scenario(write_json(w.path("sc.json"), {mode: block}), mode, T12)

    def test_gather_hold_mang_ca_the(self):
        with Workdir() as w:
            self.assertEqual(self.load(w, {"hold": [item(1, fresh=30)]}, "gather")["hold"][0]["id"], "I1")
            for bad in ({"hold": ["ca_loc"]}, {"hold": [item(1), item(1)]},
                        {"hold": [item(i) for i in range(1, 14)]}, {"hold": {"ca_loc": 1}}):
                with self.assertRaises(BadInput, msg=bad):
                    self.load(w, bad, "gather")

    def test_quan_stock_va_reserved_theo_id(self):
        stock = [item(1, "ca_loc", 90), item(2, "ca_loc", 20), item(3, "bong_sung"), item(4, "bong_sung")]
        cus = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}
        with Workdir() as w:
            self.load(w, {"stock": stock, "customers": [dict(cus, reserved=["I1"])]}, "quan")
            self.load(w, {"stock": stock, "customers": [cus]}, "quan")  # bỏ reserved -> sim tự cấp
            goi = {"id": "C2", "table_id": "T2", "dish_id": "goi_bong_sung", "reserved": ["I3", "I4"]}
            self.load(w, {"stock": stock, "customers": [dict(cus, reserved=["I1"]), goi]}, "quan")
            bads = [
                {"stock": {"ca_loc": 1}},                                              # kho đếm cũ
                {"stock": stock, "customers": [dict(cus, reserved={"ca_loc": 1})]},    # reserved kiểu cũ
                {"stock": stock, "customers": [dict(cus, reserved=["I9"])]},           # id lạ
                {"stock": stock, "customers": [dict(cus, reserved=["I2"])]},           # trỏ hàng ươn
                {"stock": stock, "customers": [dict(cus, reserved=["I3"])]},           # sai công thức
                {"stock": stock, "customers": [dict(cus, reserved=["I1"]),
                                               dict(goi, dish_id="ca_loc_nuong_trui", reserved=["I1"])]},  # dùng chung
                {"stock": stock, "customers": [dict(cus, order_status="unfulfillable", reserved=["I1"])]},
                {"stock": [item(1, "ca_loc"), item(1, "bong_sung")]},                  # id trùng
            ]
            for bad in bads:
                with self.assertRaises(BadInput, msg=bad):
                    self.load(w, bad, "quan")


class GatherV12(unittest.TestCase):
    def sim(self, scenario):
        return GatherSim(T12, dict({"random_fish": False, "monsters": []}, **scenario), Streams(1), IdAllocator())

    def test_hang_moi_la_ca_the_id_noi_tiep(self):
        s = self.sim({"hold": [item(5, "ca_loc", 70)]})
        self.assertTrue(s._add_to_hold(["ca_linh"] * 3))
        self.assertEqual([i["id"] for i in s.hold], ["I5", "I6", "I7", "I8"])
        self.assertEqual(s.hold[1], {"id": "I6", "kind": "ca_linh", "fresh": 100.0})
        self.assertEqual(s.snapshot()["hold"][0], {"id": "I5", "kind": "ca_loc", "fresh": 70.0})
        self.assertEqual([i["id"] for i in s.inventory_items()], ["I5", "I6", "I7", "I8"])

    def test_lost_la_mang_ca_the_lifo_khi_bi_can_va_ngat(self):
        hold = [item(1, "ca_loc"), item(2, "bong_sung", 80), item(3, "ca_linh", 60), item(4, "keo_neo", 50)]
        croc = {"id": "M1", "kind": "ca_sau", "pos": [51, 20], "waypoints": [[51, 20], [55, 20]]}
        s = self.sim({"player": {"pos": [50, 20], "hp": 2}, "hold": hold, "monsters": [croc]})
        from chonoi.inputs import InputState
        ev = s.step(InputState((0.0, 0.0), {}, set()))
        hit = [d for n, d in ev if n == "monster_hit"][0]
        self.assertEqual(hit["lost"], [item(4, "keo_neo", 50), item(3, "ca_linh", 60)])
        s.invuln_ticks = 0
        s.monsters[0].update(state="patrol", state_ticks_left=0, recoil_dir=None, pos=[50.5, 20])
        ev = s.step(InputState((0.0, 0.0), {}, set()))
        # cú cắn thứ hai: rơi floor(2/2) = 1 (I2) trong monster_hit, rồi faint bỏ phần còn lại (I1)
        self.assertEqual([d for n, d in ev if n == "monster_hit"][0]["lost"], [item(2, "bong_sung", 80)])
        faint = [d for n, d in ev if n == "faint"][0]
        self.assertEqual((faint["cause"], faint["lost"]), ("monster", [item(1, "ca_loc")]))
        self.assertEqual([d for n, d in ev if n == "gather_end"][0]["inventory"], {"items": []})


class HeadlessV12(unittest.TestCase):
    def test_smoke_ban_giao_file_ca_the_va_kho_dem_ma_2(self):
        with V12Headless() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"hold": [item(1, "ca_linh", 100), item(2, "ca_loc", 97.5)],
                                                           "random_fish": False, "monsters": []}})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            kho = w.path("kho.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1", "--scenario", sc,
                                     "--inputs", inp, "--inventory-out", kho, "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            with open(kho, encoding="utf-8") as f:
                saved = json.load(f)
            end = events(read_jsonl(w.path("g.jsonl")), "gather_end")[0]["data"]
            self.assertEqual(end["inventory"], saved)
            self.assertEqual([(i["id"], i["kind"]) for i in saved["items"]], [("I1", "ca_linh"), ("I2", "ca_loc")])
            self.assertEqual(snapshots(read_jsonl(w.path("g.jsonl")))[0]["hold"][1], item(2, "ca_loc", 97.5))
            dem = write_json(w.path("dem.json"), {"items": {"ca_loc": 1}})
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", dem,
                                          "--out", w.path("q.jsonl"))[0], 2, "v1.2: kho đếm cũ -> mã 2")
            old = write_json(w.path("old.json"), {"gather": {"hold": ["ca_loc"]}})
            self.assertEqual(run_headless("--mode", "gather", "--seed", "1", "--ticks", "0", "--scenario", old,
                                          "--out", w.path("x.jsonl"))[0], 2, "v1.2: scenario giỏ kiểu cũ -> mã 2")

    def test_ngat_ghi_kho_rong_v12(self):
        with V12Headless() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [50, 20], "oxygen_ticks": 0,
                                                                      "zero_oxy_ticks": 59, "hp": 1},
                                                           "hold": [item(1)], "random_fish": False, "monsters": []}})
            kho = w.path("kho.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5", "--scenario", sc,
                                     "--inventory-out", kho, "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            with open(kho, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": []})
            faint = events(read_jsonl(w.path("g.jsonl")), "faint")[0]["data"]
            self.assertEqual(faint["lost"], [item(1, fresh=100)])


if __name__ == "__main__":
    unittest.main()
