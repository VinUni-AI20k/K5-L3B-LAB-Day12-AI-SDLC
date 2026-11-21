"""Lát 1 (gather): dive/surface, oxy, oxygen_empty, ngạt/choke, Máu, faint — PRD-0 mục F, Gather bước 2.

Test hộp đen qua headless_cmd. Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_gather_lat1 -v
"""

import json
import unittest

from helpers import Workdir, events, frames, kinds_of, read_jsonl, run_headless, snapshots, write_json

OXY_MAX = 30 * 60  # oxygen_max_s × 60


def run_gather(w, block, ticks, inputs=None, inv_out=None):
    sc = write_json(w.path("sc.json"), {"gather": block})
    args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--scenario", sc,
            "--snapshot-every", "1", "--out", w.path("o.jsonl")]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    if inv_out:
        args += ["--inventory-out", w.path(inv_out)]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path("o.jsonl"))


def snap_at(rows, tick):
    return next(s for s in snapshots(rows) if s["tick"] == tick)


class Oxygen(unittest.TestCase):
    def test_duoi_nuoc_tru_1_moi_tick(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [20, 10]}}, 10)
            self.assertEqual(snap_at(rows, 10)["player"]["oxygen_ticks"], OXY_MAX - 10)

    def test_mat_nuoc_hoi_6_va_kep_toi_da(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [20, 0], "oxygen_ticks": 100}}, 1)
            self.assertEqual(snap_at(rows, 1)["player"]["oxygen_ticks"], 106)
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [20, 0], "oxygen_ticks": OXY_MAX - 2}}, 1)
            self.assertEqual(snap_at(rows, 1)["player"]["oxygen_ticks"], OXY_MAX)

    def test_oxygen_empty_khi_vua_cham_0(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [20, 10], "oxygen_ticks": 3}}, 10)
            ev = events(rows, "oxygen_empty")
            self.assertEqual([(e["tick"], e["data"]) for e in ev], [(3, {"oxygen_ticks": 0})])
            self.assertEqual(snap_at(rows, 10)["player"]["oxygen_ticks"], 0)


class DiveSurface(unittest.TestCase):
    def test_dive_roi_surface_khi_doi_phia_bien(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [20, 0]}}, 60,
                              [{"tick": 0, "move": [0, 1]}, {"tick": 20, "move": [0, -1]}])
            dive, surf = events(rows, "dive"), events(rows, "surface")
            self.assertEqual(len(dive), 1)
            self.assertEqual(len(surf), 1)
            self.assertLess(dive[0]["tick"], surf[0]["tick"])
            self.assertGreater(dive[0]["data"]["pos"][1], 0.5)
            self.assertLessEqual(surf[0]["data"]["pos"][1], 0.5)
            self.assertEqual(dive[0]["data"]["pos"], snap_at(rows, dive[0]["tick"])["player"]["pos"])

    def test_khong_phat_khi_o_yen_mot_phia(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [20, 10]}}, 30, [{"tick": 0, "move": [1, 0]}])
            self.assertEqual(events(rows, "dive") + events(rows, "surface"), [])


class Choke(unittest.TestCase):
    def test_ngat_lan_dau_o_t_cong_59(self):
        """Oxy chạm 0 ở tick 3 (đếm ban đầu 0) -> choke ở tick 3 + 59 = 62, hp 3 -> 2."""
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [20, 10], "oxygen_ticks": 3}}, 130)
            ch = events(rows, "choke")
            self.assertEqual([(e["tick"], e["data"]) for e in ch[:2]], [(62, {"hp": 2}), (122, {"hp": 1})])
            self.assertEqual(snap_at(rows, 62)["player"]["zero_oxy_ticks"], 0)
            self.assertEqual(snap_at(rows, 61)["player"]["zero_oxy_ticks"], 59)

    def test_noi_dung_buoc_dang_le_ngat_thi_khong_ngat(self):
        with Workdir() as w:
            block = {"player": {"pos": [20, 0.55], "vel": [0, -4], "oxygen_ticks": 0, "zero_oxy_ticks": 59}}
            rows = run_gather(w, block, 1, [{"tick": 0, "move": [0, -1]}])
            self.assertEqual(events(rows, "choke"), [])
            self.assertEqual(len(events(rows, "surface")), 1)
            p = snap_at(rows, 1)["player"]
            self.assertEqual((p["hp"], p["oxygen_ticks"], p["zero_oxy_ticks"]), (3, 6, 0))

    def test_o_lai_duoi_nuoc_thi_ngat_ngay(self):
        with Workdir() as w:
            block = {"player": {"pos": [20, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59}}
            rows = run_gather(w, block, 1)
            self.assertEqual([(e["tick"], e["data"]) for e in events(rows, "choke")], [(1, {"hp": 2})])


class Faint(unittest.TestCase):
    def test_mau_ve_0_bo_gio_lifo_va_ket_thuc_fainted(self):
        with Workdir() as w:
            block = {"player": {"pos": [20, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                     "hold": ["ca_loc", "bong_sung", "ca_linh"]}
            rows = run_gather(w, block, 50, inv_out="inv.json")
            names = [r["name"] for r in events(rows)]
            self.assertEqual(names, ["choke", "faint", "gather_end"])
            faint = events(rows, "faint")[0]
            self.assertEqual(faint["data"]["cause"], "choke")
            self.assertEqual(faint["data"]["hp"], 0)
            self.assertEqual(kinds_of(faint["data"]["lost"]), ["ca_linh", "bong_sung", "ca_loc"])
            self.assertEqual([it["id"] for it in faint["data"]["lost"]], ["I3", "I2", "I1"])
            for it in faint["data"]["lost"]:
                self.assertAlmostEqual(it["fresh"], 100 - 1 / 120, places=3)
            end = events(rows, "gather_end")[0]
            self.assertEqual(end["data"], {"reason": "fainted", "inventory": {"items": []}})
            last = snapshots(rows)[-1]
            self.assertEqual((last["tick"], last["hold"], last["player"]["hp"]), (1, [], 0))
            self.assertEqual(rows[-1]["reason"], "fainted")
            with open(w.path("inv.json"), encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": []})

    def test_ngat_dung_buoc_bo_qua_interact(self):
        """Máu 0 thì dừng bước: interact trong bến ở cùng bước không cho docked."""
        with Workdir() as w:
            block = {"player": {"pos": [2, 1], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1}}
            rows = run_gather(w, block, 5, [{"tick": 0, "interact": True}])
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "fainted")


if __name__ == "__main__":
    unittest.main()
