"""Phase 2 gather (v1.1 mục 1.1, 4.3, 4.5): cá kèo, kèo nèo, 8 đàn đầu ca, cá bơi/đổi hướng/phản xạ, sinh cá.
Hộp đen qua headless."""

import json
import math
import unittest

from helpers import Workdir, close, events, frames, read_jsonl, run_headless, snapshots, write_json

with open("game.contract.json", encoding="utf-8") as _f:
    G = json.load(_f)["tuning"]["gather"]


def run_g(w, scenario=None, fr=(), ticks=0, code_expected=0, seed="1"):
    args = ["--mode", "gather", "--seed", seed, "--ticks", str(ticks), "--out", w.path("o.jsonl"),
            "--snapshot-every", "1"]
    if scenario is not None:
        args += ["--scenario", write_json(w.path("sc.json"), {"gather": scenario})]
    if fr:
        args += ["--inputs", write_json(w.path("in.json"), frames(*fr))]
    code, err = run_headless(*args)
    assert code == code_expected, err
    return read_jsonl(w.path("o.jsonl")) if code == 0 else None


def snap_at(rows, tick):
    return next(s for s in snapshots(rows) if s["tick"] == tick)


def fish_by_id(snap):
    return {f["id"]: f for f in snap["fish"]}


F = lambda i, kind, x, d, h=0, **kw: {"id": i, "kind": kind, "pos": [x, d], "heading_deg": h, **kw}
FAR = {"pos": [2, 0]}  # người chơi đứng ở bến, xa mọi đàn


class InitialSchools(unittest.TestCase):
    def test_8_dan_o_8_diem_sinh_khac_nhau(self):
        with Workdir() as w:
            s = snapshots(run_g(w))[0]
            self.assertEqual(len(s["fish"]), G["fish_initial"])
            self.assertEqual([f["id"] for f in s["fish"]], [f"F{i}" for i in range(1, 9)])
            pos = [tuple(f["pos"]) for f in s["fish"]]
            self.assertEqual(len(set(pos)), 8)
            for f in s["fish"]:
                self.assertIn(f["pos"][0], G["fish_spawn_x"])
                self.assertIn(f["pos"][1], G["fish_spawn_depths"][f["kind"]])
                self.assertEqual(f["age_ticks"], 0)

    def test_nhieu_seed_khong_trung_diem(self):
        for seed in range(1, 21):  # một seed có thể tình cờ không trùng; 20 seed thì luật cách > 1 m phải có tác dụng
            with Workdir() as w:
                pos = [tuple(f["pos"]) for f in snapshots(run_g(w, seed=str(seed)))[0]["fish"]]
                self.assertEqual(len(set(pos)), 8, f"seed {seed}: {pos}")

    def test_cung_seed_giong_tung_byte_khac_seed_khac(self):
        outs = []
        for seed in ("7", "7", "8"):
            with Workdir() as w:
                run_g(w, ticks=800, seed=seed)
                with open(w.path("o.jsonl"), "rb") as f:
                    outs.append(f.read())
        self.assertEqual(outs[0], outs[1])
        self.assertNotEqual(outs[0], outs[2])


class Swim(unittest.TestCase):
    def test_random_fish_false_ca_dung_yen_khong_sinh(self):
        with Workdir() as w:
            rows = run_g(w, {"player": FAR, "random_fish": False, "fish": [F("F1", "ca_linh", 50, 5)]}, ticks=400)
            self.assertEqual(snapshots(rows)[-1]["fish"][0]["pos"], [50, 5])
            self.assertEqual(events(rows, "fish_spawned"), [])

    def test_toc_do_1_5_m_s_va_age_ticks(self):
        with Workdir() as w:
            rows = run_g(w, {"player": FAR, "fish": [F("F1", "ca_linh", 50, 5)]}, ticks=60)
            f = fish_by_id(snap_at(rows, 60))["F1"]
            self.assertTrue(close(f["pos"][0], 51.5, 0.001) and close(f["pos"][1], 5, 0.001), f)
            self.assertEqual(f["age_ticks"], 60)

    def test_doi_huong_o_buoc_boi_thu_120(self):
        with Workdir() as w:
            rows = run_g(w, {"player": FAR, "fish": [F("F1", "ca_linh", 30, 7)]}, ticks=121)
            self.assertEqual(fish_by_id(snap_at(rows, 119))["F1"]["heading_deg"], 0)
            h120 = fish_by_id(snap_at(rows, 120))["F1"]["heading_deg"]
            self.assertNotEqual(h120, 0)
            self.assertEqual(fish_by_id(snap_at(rows, 121))["F1"]["heading_deg"], h120)

    def test_age_ticks_fixture_119_doi_huong_ngay_buoc_dau(self):
        with Workdir() as w:
            rows = run_g(w, {"player": FAR, "fish": [F("F1", "ca_linh", 30, 7, age_ticks=119)]}, ticks=1)
            self.assertNotEqual(fish_by_id(snap_at(rows, 1))["F1"]["heading_deg"], 0)

    def test_phan_xa_mep_x(self):
        with Workdir() as w:
            rows = run_g(w, {"player": FAR, "fish": [F("F1", "ca_linh", 95.99, 5)]}, ticks=1)
            f = fish_by_id(snap_at(rows, 1))["F1"]
            self.assertTrue(close(f["pos"][0], 95.985, 0.0011), f)  # 95.99 + 0.025 = 96.015 -> 96 - 0.015
            self.assertEqual(f["heading_deg"], 180)

    def test_phan_xa_goc_dao_ca_hai(self):
        with Workdir() as w:
            rows = run_g(w, {"player": FAR, "fish": [F("F1", "ca_linh", 95.99, 11.99, 45)]}, ticks=1)
            f = fish_by_id(snap_at(rows, 1))["F1"]
            self.assertEqual(f["heading_deg"], 225)
            self.assertLess(f["pos"][0], 96)
            self.assertLess(f["pos"][1], 12)

    def test_ca_keo_o_dai_sau_khong_vuot_bien(self):
        with Workdir() as w:
            rows = run_g(w, {"player": FAR, "fish": [F("F1", "ca_keo", 50, 27.9, 90)]}, ticks=300)
            for s in snapshots(rows):
                d = fish_by_id(s)["F1"]["pos"][1]
                self.assertTrue(22 <= d <= 28, d)


class CatchBeforeSwim(unittest.TestCase):
    def test_bat_theo_vi_tri_truoc_khi_ca_boi(self):
        with Workdir() as w:
            # cá ở 2.01 m (ngoài tầm) đang bơi lại gần: bước này vẫn bắt hụt
            rows = run_g(w, {"player": {"pos": [20, 5]}, "fish": [F("F1", "ca_linh", 22.01, 5, 180)]},
                         [{"tick": 0, "catch": True}], ticks=1)
            self.assertEqual(events(rows, "fish_caught"), [])
        with Workdir() as w:
            # cá ở 1.99 m đang bơi ra xa: bước này vẫn bắt được
            rows = run_g(w, {"player": {"pos": [20, 5]}, "fish": [F("F1", "ca_linh", 21.99, 5, 0)]},
                         [{"tick": 0, "catch": True}], ticks=1)
            self.assertEqual(events(rows, "fish_caught")[0]["data"]["fish_id"], "F1")

    def test_bat_ca_keo_yield_2(self):
        with Workdir() as w:
            rows = run_g(w, {"player": {"pos": [40, 25]}, "random_fish": False,
                             "fish": [F("F1", "ca_keo", 41, 25)]}, [{"tick": 0, "catch": True}], ticks=1)
            self.assertEqual(events(rows, "fish_caught")[0]["data"], {"fish_id": "F1", "kind": "ca_keo", "yield": 2})

    def test_hai_keo_neo_o_N5(self):
        with Workdir() as w:
            rows = run_g(w, {"player": {"pos": [76, 0]}, "random_fish": False}, [{"tick": 0, "interact": True}], ticks=1)
            self.assertEqual(events(rows, "gather")[0]["data"], {"node_id": "N5", "kind": "keo_neo", "amount": 1})


class Spawn(unittest.TestCase):
    def test_sinh_dung_tick_360_cach_moi_dan_hon_1m(self):
        with Workdir() as w:
            rows = run_g(w, {"player": FAR, "fish": [F("F1", "ca_loc", 15, 10)]}, ticks=721)
            sp = events(rows, "fish_spawned")
            self.assertEqual([e["tick"] for e in sp], [360, 720])
            self.assertEqual([e["data"]["id"] for e in sp], ["F2", "F3"])
            e = sp[0]["data"]
            self.assertIn(e["pos"][0], G["fish_spawn_x"])
            self.assertIn(e["pos"][1], G["fish_spawn_depths"][e["kind"]])
            others = [f for f in snap_at(rows, 360)["fish"] if f["id"] != "F2"]
            self.assertTrue(all(math.dist(e["pos"], f["pos"]) > 1 for f in others))

    def test_ca_moi_tham_gia_tu_buoc_sau(self):
        with Workdir() as w:
            rows = run_g(w, {"player": FAR, "fish": [F("F1", "ca_loc", 15, 10)]}, ticks=361)
            self.assertEqual(fish_by_id(snap_at(rows, 360))["F2"]["age_ticks"], 0)
            self.assertEqual(fish_by_id(snap_at(rows, 361))["F2"]["age_ticks"], 1)

    def test_du_tran_12_dan_khong_sinh(self):
        with Workdir() as w:
            fish = [F(f"F{i}", "ca_linh", 10 + 6 * i, 6) for i in range(1, 13)]
            rows = run_g(w, {"player": FAR, "fish": fish}, ticks=360)
            self.assertEqual(events(rows, "fish_spawned"), [])

    def test_het_gio_truoc_khi_sinh_thi_khong_sinh(self):
        with Workdir() as w:
            rows = run_g(w, {"player": FAR, "time_left_ticks": 360, "fish": [F("F1", "ca_loc", 15, 10)]}, ticks=400)
            self.assertEqual(events(rows, "fish_spawned"), [])
            self.assertEqual(rows[-1]["reason"], "time")


class ScenarioValidation(unittest.TestCase):
    def test_ca_boi_ngoai_mien_loai_ma_2(self):
        with Workdir() as w:
            run_g(w, {"fish": [F("F1", "ca_keo", 50, 5)]}, code_expected=2)

    def test_ca_dung_yen_ngoai_mien_loai_hop_le(self):
        with Workdir() as w:
            run_g(w, {"random_fish": False, "fish": [F("F1", "ca_keo", 50, 5)]})

    def test_age_ticks_am_ma_2(self):
        with Workdir() as w:
            run_g(w, {"fish": [F("F1", "ca_linh", 50, 5, age_ticks=-1)]}, code_expected=2)


if __name__ == "__main__":
    unittest.main()
