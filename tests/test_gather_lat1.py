"""Lát 1 (gather): dive/surface, oxy, ngạt, Máu, ngất. Test HỘP ĐEN qua headless_cmd.

Đối chiếu docs/prd/phase-1.md, mục F "Gather" bước 2 và mục E (sự kiện). Số liệu đọc từ game.contract.json.
Chạy riêng: PYTHONPATH=tests:. python3 -m unittest tests.test_gather_lat1 -v
"""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def tuning_gather():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


def run_gather(w, block, ticks, inputs=None, inventory_out=None, every=1, out="o.jsonl"):
    """Chạy gather với scenario `block` (cá mặc định tắt để không nhiễu); trả các dòng JSONL."""
    block = dict({"random_fish": False}, **block)
    args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--scenario",
            write_json(w.path("sc.json"), {"gather": block}), "--snapshot-every", str(every), "--out", w.path(out)]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    if inventory_out:
        args += ["--inventory-out", inventory_out]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path(out))


def oxygen_events(rows):
    names = ("dive", "surface", "oxygen_empty", "choke", "faint", "gather_end")
    return [(r["tick"], r["name"]) for r in rows if r["type"] == "event" and r["name"] in names]


class Oxygen(unittest.TestCase):
    def test_duoi_nuoc_tru_1_moi_tick(self):
        g = tuning_gather()
        omax = int(round(g["oxygen_max_s"] * 60))
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10]}}, 10)
            s = {r["tick"]: r["player"] for r in snapshots(rows)}
            for k in range(11):
                self.assertEqual(s[k]["oxygen_ticks"], omax - k, k)
                self.assertFalse(s[k]["at_surface"])

    def test_mat_nuoc_hoi_va_kep_toi_da(self):
        g = tuning_gather()
        omax, refill = int(round(g["oxygen_max_s"] * 60)), g["oxygen_refill_per_tick"]
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 0], "oxygen_ticks": omax - refill - 4}}, 3)
            s = {r["tick"]: r["player"]["oxygen_ticks"] for r in snapshots(rows)}
            self.assertEqual([s[0], s[1], s[2], s[3]], [omax - refill - 4, omax - 4, omax, omax])

    def test_dung_mep_surface_depth_tinh_la_mat_nuoc(self):
        g = tuning_gather()
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, g["surface_depth"]], "oxygen_ticks": 100}}, 1)
            p = snapshots(rows)[-1]["player"]
            self.assertTrue(p["at_surface"])
            self.assertEqual(p["oxygen_ticks"], 100 + g["oxygen_refill_per_tick"])

    def test_oxygen_empty_dung_mot_lan_khi_tu_duong_ve_0(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10], "oxygen_ticks": 3}}, 20, every=5)
            ev = events(rows, "oxygen_empty")
            self.assertEqual([e["tick"] for e in ev], [3])
            self.assertEqual(ev[0]["data"], {"oxygen_ticks": 0})

    def test_khong_oxygen_empty_khi_da_bang_0_tu_dau(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10], "oxygen_ticks": 0}}, 5)
            self.assertEqual(events(rows, "oxygen_empty"), [])
            self.assertEqual(snapshots(rows)[-1]["player"]["zero_oxy_ticks"], 5)


class Choke(unittest.TestCase):
    def test_cham_0_o_t_thi_ngat_o_t_cong_59(self):
        """oxy 1 -> chạm 0 ở tick 1 (đếm ngạt = 1 ngay bước đó) -> choke lần đầu ở tick 60."""
        g = tuning_gather()
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10], "oxygen_ticks": 1}}, 130, every=10)
            self.assertEqual(events(rows, "oxygen_empty")[0]["tick"], 1)
            chokes = events(rows, "choke")
            interval = g["choke_interval_ticks"]
            self.assertEqual([e["tick"] for e in chokes], [1 + interval - 1, 1 + 2 * interval - 1])
            self.assertEqual([e["data"] for e in chokes], [{"hp": g["hp_max"] - 1}, {"hp": g["hp_max"] - 2}])
            s = {r["tick"]: r["player"] for r in snapshots(rows)}
            self.assertEqual(s[60]["zero_oxy_ticks"], 0, "đủ ngưỡng thì đếm lại từ 0")
            self.assertEqual(s[70]["zero_oxy_ticks"], 10)

    def test_noi_len_dung_buoc_dang_le_ngat_thi_khong_ngat(self):
        g = tuning_gather()
        base = {"pos": [50, g["surface_depth"] + 0.02], "oxygen_ticks": 0, "zero_oxy_ticks": 59}
        with Workdir() as w:
            # đứng yên dưới nước: ngạt ngay bước đầu
            rows = run_gather(w, {"player": dict(base)}, 1)
            self.assertEqual([e["tick"] for e in events(rows, "choke")], [1])
            # đang bơi lên với vận tốc đủ để qua biên trong bước đầu: surface, hồi oxy, không ngạt
            rows = run_gather(w, {"player": dict(base, vel=[0, -g["swim_speed"]])}, 1,
                              inputs=[{"tick": 0, "move": [0, -1]}])
            self.assertEqual(events(rows, "choke"), [])
            self.assertEqual([e["name"] for e in events(rows)], ["surface"])
            p = snapshots(rows)[-1]["player"]
            self.assertEqual((p["oxygen_ticks"], p["zero_oxy_ticks"], p["hp"]),
                             (g["oxygen_refill_per_tick"], 0, g["hp_max"]))


class Faint(unittest.TestCase):
    def test_het_mau_bo_gio_lifo_va_kho_rong(self):
        with Workdir() as w:
            inv = w.path("kho.json")
            rows = run_gather(w, {"player": {"pos": [50, 10], "oxygen_ticks": 1, "hp": 1},
                                  "hold": ["ca_loc", "bong_sung", "ca_linh"]}, 200, inventory_out=inv)
            self.assertEqual(oxygen_events(rows), [(1, "oxygen_empty"), (60, "choke"), (60, "faint"), (60, "gather_end")])
            self.assertEqual(events(rows, "choke")[0]["data"], {"hp": 0})
            self.assertEqual(events(rows, "faint")[0]["data"],
                             {"cause": "choke", "lost": ["ca_linh", "bong_sung", "ca_loc"], "hp": 0})
            self.assertEqual(events(rows, "gather_end")[0]["data"], {"reason": "fainted", "inventory": {"items": {}}})
            last = snapshots(rows)[-1]
            self.assertEqual((last["tick"], last["state"], last["hold"], last["player"]["hp"]), (60, "finished", [], 0))
            self.assertEqual((rows[-1]["type"], rows[-1]["reason"], rows[-1]["ticks"]), ("end", "fainted", 60))
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})

    def test_ba_lan_ngat_moi_ngat_xiu(self):
        g = tuning_gather()
        interval = g["choke_interval_ticks"]
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10], "oxygen_ticks": 0}}, 1000, every=50)
            self.assertEqual([(e["tick"], e["data"]["hp"]) for e in events(rows, "choke")],
                             [(interval * i, g["hp_max"] - i) for i in range(1, g["hp_max"] + 1)])
            self.assertEqual(events(rows, "faint")[0]["data"]["lost"], [])
            self.assertEqual(rows[-1]["ticks"], interval * g["hp_max"])

    def test_ngat_xiu_thang_het_gio_cung_tick(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                                  "hold": ["ca_loc"], "time_left_ticks": 1}, 10)
            ends = events(rows, "gather_end")
            self.assertEqual(len(ends), 1)
            self.assertEqual(ends[0]["data"]["reason"], "fainted")
            self.assertEqual(rows[-1]["reason"], "fainted")

    def test_tat_dinh_tung_byte(self):
        block = {"player": {"pos": [50, 10], "oxygen_ticks": 1, "hp": 2}, "hold": ["ca_loc", "bong_sung"]}
        with Workdir() as w:
            run_gather(w, block, 200, every=7, out="a.jsonl")
            run_gather(w, block, 200, every=7, out="b.jsonl")
            with open(w.path("a.jsonl"), "rb") as a, open(w.path("b.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())


class DiveSurface(unittest.TestCase):
    def test_lan_xuong_roi_noi_len_moi_lan_doi_phia_mot_su_kien(self):
        g = tuning_gather()
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 0]}}, 120,
                              inputs=[{"tick": 0, "move": [0, 1]}, {"tick": 30, "move": [0, -1]}])
            ds = [e for e in events(rows) if e["name"] in ("dive", "surface")]
            self.assertEqual([e["name"] for e in ds], ["dive", "surface"])
            dive, surf = ds
            self.assertGreater(dive["data"]["pos"][1], g["surface_depth"])
            self.assertLessEqual(surf["data"]["pos"][1], g["surface_depth"])
            s = {r["tick"]: r["player"] for r in snapshots(rows)}
            self.assertEqual(s[dive["tick"]]["pos"], dive["data"]["pos"], "pos là vị trí sau di chuyển")
            self.assertTrue(s[dive["tick"] - 1]["at_surface"])
            self.assertFalse(s[dive["tick"]]["at_surface"])
            self.assertTrue(s[surf["tick"]]["at_surface"])

    def test_boi_ngang_duoi_nuoc_khong_phat_su_kien(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [20, 10]}}, 60, inputs=[{"tick": 0, "move": [1, 0]}], every=60)
            self.assertEqual([e for e in events(rows) if e["name"] in ("dive", "surface")], [])


if __name__ == "__main__":
    unittest.main()
