"""Test luật sinh tồn của gather (lát 1, owner: sim/gather): dive/surface, oxy, ngạt, ngất.
Kiểu hộp đen như test_smoke_p1: chạy headless với scenario, đọc JSONL.

Chạy: PYTHONPATH=tests:. python3 -m unittest test_gather_sinh_ton -v
"""

import json
import unittest

from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json, frames


def run_gather(w, scenario, ticks, inputs=None, inventory=False):
    sc = write_json(w.path("sc.json"), {"gather": scenario})
    args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--scenario", sc,
            "--snapshot-every", "1", "--out", w.path("o.jsonl")]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    if inventory:
        args += ["--inventory-out", w.path("inv.json")]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path("o.jsonl"))


def by_tick(rows):
    return {r["tick"]: r["player"] for r in snapshots(rows)}


class Survival(unittest.TestCase):
    def test_dive_khi_roi_mat_nuoc(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 0]}}, 30,
                              inputs=[{"tick": 0, "move": [0, 1]}])
            d = events(rows, "dive")
            self.assertEqual(len(d), 1)
            self.assertGreater(d[0]["data"]["pos"][1], 0.5)
            self.assertEqual(events(rows, "surface"), [])

    def test_surface_khi_noi_len(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 2]}}, 60,
                              inputs=[{"tick": 0, "move": [0, -1]}])
            s = events(rows, "surface")
            self.assertEqual(len(s), 1)
            self.assertLessEqual(s[0]["data"]["pos"][1], 0.5)
            self.assertEqual(events(rows, "dive"), [])

    def test_oxy_giam_moi_tick_duoi_nuoc(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10], "oxygen_ticks": 100}}, 10)
            p = by_tick(rows)
            self.assertEqual(p[10]["oxygen_ticks"], 90)

    def test_oxy_hoi_moi_tick_o_mat_nuoc_va_kep_max(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 0], "oxygen_ticks": 100}}, 5)
            self.assertEqual(by_tick(rows)[5]["oxygen_ticks"], 130)
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 0], "oxygen_ticks": 1795}}, 5)
            self.assertEqual(by_tick(rows)[5]["oxygen_ticks"], 1800)

    def test_oxygen_empty_dung_dung_mot_lan(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10], "oxygen_ticks": 2}}, 5)
            e = events(rows, "oxygen_empty")
            self.assertEqual(len(e), 1)
            self.assertEqual(e[0]["tick"], 2)
            self.assertEqual(by_tick(rows)[5]["oxygen_ticks"], 0)

    def test_ngat_mat_1_mau_dung_choke_interval(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10], "oxygen_ticks": 0}}, 62)
            p = by_tick(rows)
            self.assertEqual(p[59]["hp"], 3)
            self.assertEqual(p[60]["hp"], 2)
            self.assertEqual(p[60]["zero_oxy_ticks"], 0)
            self.assertEqual(len(events(rows, "choke")), 1)
            self.assertEqual(events(rows, "choke")[0]["data"]["hp"], 2)

    def test_hoi_oxy_reset_bo_dem_ngat(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 0.6], "oxygen_ticks": 0, "zero_oxy_ticks": 50}}, 30,
                              inputs=[{"tick": 0, "move": [0, -1]}])
            p = by_tick(rows)
            self.assertLessEqual(p[30]["pos"][1], 0.5)
            self.assertEqual(p[30]["zero_oxy_ticks"], 0)
            self.assertEqual(p[30]["hp"], 3)

    def test_invuln_chan_ngat(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10], "oxygen_ticks": 0, "invuln_ticks": 1000}}, 62)
            self.assertEqual(by_tick(rows)[62]["hp"], 3)
            self.assertEqual(events(rows, "choke"), [])

    def test_mau_ve_0_ngat_xiu_mat_gio(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                                  "hold": ["ca_loc", "ca_linh"]}, 100, inventory=True)
            self.assertEqual(len(events(rows, "faint")), 1)
            self.assertEqual(events(rows, "faint")[0]["tick"], 1)
            end = events(rows, "gather_end")
            self.assertEqual(len(end), 1)
            self.assertEqual(end[0]["data"]["reason"], "fainted")
            self.assertEqual(end[0]["data"]["inventory"], {"items": {}})
            self.assertEqual(rows[-1]["reason"], "fainted")
            with open(w.path("inv.json"), encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})


class Hold(unittest.TestCase):
    """Giỏ: thứ tự nhặt (cuối mảng = mới nhất), sức chứa hold_capacity (12). Việc NHẶT (hold_full khi nhặt)
    thuộc lát 2; ở đây kiểm phần đã có: snapshot giữ thứ tự, sức chứa được kiểm, ngất/hết giờ xử lý giỏ."""

    def test_snapshot_giu_thu_tu_nhat_lifo(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10]}, "hold": ["ca_loc", "ca_linh", "ca_loc"]}, 1)
            s = snapshots(rows)[0]
            self.assertEqual(s["hold"], ["ca_loc", "ca_linh", "ca_loc"])
            self.assertEqual(s["hold_count"], 3)
            self.assertEqual(s["hold_capacity"], 12)

    def test_giỏ_day_12_chap_nhan_va_tren_12_tu_choi(self):
        full = ["ca_linh"] * 12
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10]}, "hold": full}, 1)
            s = snapshots(rows)[0]
            self.assertEqual(s["hold_count"], 12)
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"hold": full + ["ca_loc"]}})
            code, _ = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1", "--scenario", sc,
                                   "--out", w.path("o.jsonl"))
            self.assertEqual(code, 2)

    def test_het_gio_ghi_kho_theo_so_luong_trong_gio(self):
        with Workdir() as w:
            hold = ["ca_loc", "ca_linh", "ca_loc", "bong_sung"]
            rows = run_gather(w, {"player": {"pos": [50, 10]}, "hold": hold, "time_left_ticks": 2}, 5, inventory=True)
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "time")
            with open(w.path("inv.json"), encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"bong_sung": 1, "ca_linh": 1, "ca_loc": 2}})

    def test_ngat_giỏ_day_mat_het(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                                  "hold": ["ca_linh"] * 12}, 3, inventory=True)
            self.assertEqual(events(rows, "gather_end")[0]["data"]["inventory"], {"items": {}})


if __name__ == "__main__":
    unittest.main()
